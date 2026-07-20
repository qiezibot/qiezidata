# -*- coding: utf-8 -*-
"""
File Manager - Eggplant Data v2.1
Multi-user + Admin Dashboard + File Management
"""
import os, uuid, mimetypes, sqlite3, secrets, hashlib
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse

DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI(title='Eggplant Data (Railway)', version='2.1')

# ===== Database =====
use_pg = bool(DATABASE_URL)
db_pool = None
import asyncio

async def init_db():
    global db_pool
    if use_pg:
        import asyncpg
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with db_pool.acquire() as conn:
            await conn.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL, password_hash VARCHAR(128) NOT NULL, display_name VARCHAR(128), created_at TIMESTAMP NOT NULL DEFAULT NOW(), role VARCHAR(16) NOT NULL DEFAULT \'user\')')
            # 迁移：给旧 users 表添加 role 列
            ucols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
            if 'role' not in [c['column_name'] for c in ucols]:
                await conn.execute("ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'user'")
            cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='files'")
            if 'user_id' not in [c['column_name'] for c in cols]:
                await conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
                admin = await conn.fetchrow("SELECT id FROM users WHERE username='admin'")
                if not admin:
                    h = _hash('admin123')
                    await conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)", 'admin', h, 'Admin', 'admin')
                    aid = await conn.fetchval("SELECT id FROM users WHERE username='admin'")
                else: aid = admin['id']
                await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)
            if not cols:
                await conn.execute('CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL, size BIGINT NOT NULL, mime_type VARCHAR(128), upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL)')
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, display_name TEXT, created_at TEXT NOT NULL, role TEXT NOT NULL DEFAULT \'user\')')
        # 迁移：给旧 users 表添加 role 列
        ucur = conn.execute("PRAGMA table_info(users)")
        ucols = [r[1] for r in ucur.fetchall()]
        if 'role' not in ucols:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
        cur = conn.execute("PRAGMA table_info(files)")
        cols = [r[1] for r in cur.fetchall()]
        if 'user_id' not in cols:
            conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
            admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
            if not admin:
                h = _hash('admin123')
                conn.execute("INSERT INTO users (username,password_hash,display_name,created_at,role) VALUES (?,?,?,?,?)",('admin',h,'Admin',datetime.utcnow().isoformat(),'admin'))
                aid = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
            else: aid = admin[0]
            conn.execute('UPDATE files SET user_id = ? WHERE user_id IS NULL', (aid,))
        if not cols:
            conn.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, filename TEXT NOT NULL, original_name TEXT NOT NULL, size INTEGER NOT NULL, mime_type TEXT, upload_time TEXT NOT NULL, file_path TEXT NOT NULL)')
        conn.commit(); conn.close()

@app.on_event('startup')
async def startup(): await init_db()

# ===== Helpers =====
async def db_fetch(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn: return await conn.fetch(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db'); conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall(); conn.close(); return rows
async def db_fetchrow(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn: return await conn.fetchrow(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db'); conn.row_factory = sqlite3.Row
        row = conn.execute(sql, params).fetchone(); conn.close(); return row
async def db_execute(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn: return await conn.execute(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db'); cur = conn.execute(sql, params); conn.commit(); conn.close(); return cur
async def db_fetchval(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn: return await conn.fetchval(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db'); val = conn.execute(sql, params).fetchone()[0]; conn.close(); return val

AUTH_COOKIE = 'eggplant_token'
def _hash(pw):
    s = secrets.token_hex(16); return s + ':' + hashlib.sha256((s + pw).encode()).hexdigest()
def _verify(pw, stored):
    s, h = stored.split(':', 1); return h == hashlib.sha256((s + pw).encode()).hexdigest()
def _token(uid):
    sig = hashlib.sha256(f'{uid}:{SECRET_KEY}'.encode()).hexdigest()[:16]; return f'{uid}:{sig}'
def _parse(token):
    try:
        parts = token.split(':'); uid = int(parts[0])
        return uid if parts[1] == hashlib.sha256(f'{uid}:{SECRET_KEY}'.encode()).hexdigest()[:16] else None
    except: return None
def _auth(request): return _parse(request.cookies.get(AUTH_COOKIE, ''))
def _require(request):
    uid = _auth(request)
    if uid is None: raise HTTPException(status_code=401)
    return uid
async def _user(uid):
    row = await db_fetchrow('SELECT id,username,display_name,role FROM users WHERE id=$1' if use_pg else 'SELECT id,username,display_name,role FROM users WHERE id=?', uid)
    return dict(row) if row else None

# ===== Routes =====
@app.get('/')
async def home(request: Request):
    uid = _auth(request)
    if uid is None: return HTMLResponse(_LOGIN)
    user = await _user(uid)
    if not user: return HTMLResponse(_LOGIN)
    name = user.get('display_name','') or user.get('username','')
    if user.get('role') == 'admin':
        return HTMLResponse(_ADMIN.replace('<!--U-->', name))
    return HTMLResponse(_USER.replace('<!--U-->', name))

@app.post('/register')
async def register(username: str = Form(...), password: str = Form(...), display_name: str = Form(None)):
    username = username.strip()
    if len(username) < 2: return RedirectResponse(url='/?e=inv', status_code=302)
    if await db_fetchrow('SELECT id FROM users WHERE username=$1' if use_pg else 'SELECT id FROM users WHERE username=?', username):
        return RedirectResponse(url='/?e=exists', status_code=302)
    pw = _hash(password); now = datetime.utcnow().isoformat()
    if use_pg:
        await db_execute('INSERT INTO users (username,password_hash,display_name) VALUES ($1,$2,$3)', username, pw, display_name or username)
    else:
        await db_execute('INSERT INTO users (username,password_hash,display_name,created_at) VALUES (?,?,?,?)', username, pw, display_name or username, now)
    return RedirectResponse(url='/?reg=1', status_code=302)

@app.post('/login')
async def login(username: str = Form(...), password: str = Form(...)):
    row = await db_fetchrow('SELECT id,password_hash FROM users WHERE username=$1' if use_pg else 'SELECT id,password_hash FROM users WHERE username=?', username.strip())
    if not row or not _verify(password, row['password_hash']):
        return RedirectResponse(url='/?e=1', status_code=302)
    token = _token(row['id'])
    resp = RedirectResponse(url='/', status_code=302)
    resp.set_cookie(key=AUTH_COOKIE, value=token, httponly=True, max_age=86400*7, samesite='lax')
    return resp

@app.get('/logout')
async def logout():
    resp = RedirectResponse(url='/', status_code=302)
    resp.delete_cookie(AUTH_COOKIE)
    return resp

@app.get('/me')
async def get_me(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user: raise HTTPException(status_code=404)
    return user

@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    uid = _require(request)
    ext = str(Path(file.filename).suffix) if file.filename else ''
    uname = f'{uuid.uuid4().hex}{ext}'
    udir = os.path.join(UPLOAD_DIR, str(uid)); os.makedirs(udir, exist_ok=True)
    fp = os.path.join(udir, uname)
    c = await file.read()
    with open(fp, 'wb') as f: f.write(c)
    m = file.content_type or mimetypes.guess_type(str(file.filename))[0] or 'application/octet-stream'
    if use_pg:
        row = await db_fetchrow('INSERT INTO files (user_id,filename,original_name,size,mime_type,file_path) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id,upload_time', uid, uname, file.filename, len(c), m, fp)
        fid, upt = row['id'], row['upload_time'].isoformat()
    else:
        now = datetime.utcnow().isoformat()
        cur = await db_execute('INSERT INTO files (user_id,filename,original_name,size,mime_type,upload_time,file_path) VALUES (?,?,?,?,?,?,?)', uid, uname, file.filename, len(c), m, now, fp)
        fid, upt = cur.lastrowid, now
    return {'id': fid, 'filename': file.filename, 'size': len(c), 'mime': m, 'upload_time': upt}

@app.get('/files')
async def list_files(request: Request):
    uid = _require(request)
    rows = await db_fetch('SELECT id,filename,original_name,size,mime_type,upload_time FROM files WHERE user_id=$1 ORDER BY upload_time DESC' if use_pg else 'SELECT id,filename,original_name,size,mime_type,upload_time FROM files WHERE user_id=? ORDER BY upload_time DESC', uid)
    return [{**dict(r), 'upload_time': str(r['upload_time'])} for r in rows]

def _get_file(uid, fid):
    return db_fetchrow('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)

@app.get('/download/{fid}')
async def download_file(request: Request, fid: int):
    uid = _require(request)
    rows = await db_fetch('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not rows: raise HTTPException(status_code=404)
    row = rows[0]
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404)
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{fid}')
async def read_file(request: Request, fid: int):
    uid = _require(request)
    rows = await db_fetch('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not rows: raise HTTPException(status_code=404)
    row = rows[0]
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404)
    te = {'.txt','.json','.xml','.py','.js','.sh','.sql','.html','.css','.md','.csv','.log','.env'}
    if not (row['mime_type'] or '').startswith('text/') and Path(row['original_name']).suffix.lower() not in te:
        raise HTTPException(status_code=400)
    try: return PlainTextResponse(open(row['file_path'],'r',encoding='utf-8').read())
    except: raise HTTPException(status_code=400)

@app.delete('/delete/{fid}')
async def delete_file(request: Request, fid: int):
    uid = _require(request)
    rows = await db_fetch('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not rows: raise HTTPException(status_code=404)
    row = rows[0]
    if os.path.exists(row['file_path']): os.remove(row['file_path'])
    await db_execute('DELETE FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'DELETE FROM files WHERE id=? AND user_id=?', fid, uid)
    return {'message': 'ok'}

@app.get('/admin/stats')
async def admin_stats(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    u = await db_fetchval('SELECT COUNT(*) FROM users' if not use_pg else 'SELECT COUNT(*) FROM users')
    f = await db_fetchval('SELECT COUNT(*) FROM files' if not use_pg else 'SELECT COUNT(*) FROM files')
    s = await db_fetchval("SELECT COALESCE(SUM(size),0) FROM files" if not use_pg else "SELECT COALESCE(SUM(size),0) FROM files")
    a = await db_fetchval("SELECT COUNT(*) FROM users WHERE role='admin'" if not use_pg else "SELECT COUNT(*) FROM users WHERE role='admin'")
    def fm(b): return f'{b}B' if b<1024 else f'{b/1024:.1f}KB' if b<1024**2 else f'{b/1024**2:.1f}MB'
    return {'users': u, 'files': f, 'size': s, 'size_display': fm(s), 'admins': a}

@app.get('/admin/users')
async def admin_users(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch('SELECT id,username,display_name,role,created_at FROM users ORDER BY id' if not use_pg else 'SELECT id,username,display_name,role,created_at FROM users ORDER BY id')
    return [dict(r) for r in rows]

@app.get('/admin/files')
async def admin_files(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch("SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC" if not use_pg else "SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC")
    return [dict(r) for r in rows]

@app.get('/debug')
async def debug():
    h = _hash('test123')
    v = _verify('test123', h)
    v2 = _verify('wrong', h)
    u = await db_fetch('SELECT username, id FROM users LIMIT 5')
    
    # More importantly: test actual login query
    rows = await db_fetch("SELECT id,password_hash FROM users WHERE username='admin'" if use_pg else "SELECT id,password_hash FROM users WHERE username='admin'")
    login_test = {}
    if rows:
        pw = rows[0]['password_hash']
        login_test = {
            'admin_id': rows[0]['id'],
            'pw_type': str(type(pw).__name__),
            'pw_len': len(str(pw)),
            'pw_preview': str(pw)[:20] if pw else 'NULL',
            'verify_works': _verify('admin123', pw),
        }
    
    return {'_LOGIN_len': len(str(_LOGIN)),
            'use_pg': use_pg,
            'PORT': PORT,
            'hash_test': f'{h[:20]}...',
            'verify_ok': v,
            'verify_fail': not v2,
            'users': [dict(r) for r in u],
            'login_test': login_test}

@app.exception_handler(Exception)
async def exc_handler(request: Request, exc: Exception):
    from starlette.responses import JSONResponse
    return JSONResponse(status_code=getattr(exc,'status_code',500), content={'detail': str(exc.detail if hasattr(exc,'detail') else exc)})

# ===== HTML =====
_LOGIN = """\<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.95);border-radius:16px;padding:40px 36px;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:400px;width:100%;text-align:center}
.card h1{font-size:28px;color:#333;margin-bottom:4px}
.card .subtitle{color:#999;margin-bottom:24px;font-size:14px}
.tabs{display:flex;margin-bottom:24px;border-bottom:2px solid #eee}
.tab{flex:1;text-align:center;padding:10px;cursor:pointer;color:#999;font-weight:500;border-bottom:2px solid transparent;margin-bottom:-2px;font-size:14px}
.tab.active{color:#667eea;border-bottom-color:#667eea}
.form{display:none}
.form.active{display:block}
.input-group{margin-bottom:16px;text-align:left}
.input-group label{display:block;font-size:13px;color:#555;margin-bottom:4px}
.input-group input{width:100%;padding:11px 14px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none;transition:border .2s}
.input-group input:focus{border-color:#667eea}
.btn{width:100%;padding:11px;background:#667eea;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer;transition:background .2s}
.btn:hover{background:#5a6fd6}
.msg{font-size:13px;margin-top:10px;display:none;padding:8px 12px;border-radius:6px;color:#c0392b;background:#fdecea}
.msg.success{color:#27ae60;background:#eafaf1}
</style></head><body><div class="card">
<h1>茄子数据</h1><p class="subtitle">文件管理 v2.1</p>
<div class="tabs"><div class="tab active" onclick="switchTab('login')">登录</div><div class="tab" onclick="switchTab('register')">注册</div></div>
<div class="form active" id="loginForm">
<form method="post" action="/login">
<div class="input-group"><label>用户名</label><input type="text" name="username" placeholder="输入用户名" required autofocus></div>
<div class="input-group"><label>密码</label><input type="password" name="password" placeholder="输入密码" required></div>
<button class="btn" type="submit">登录</button>
</form>
<div class="msg" id="loginError">用户名或密码错误</div>
</div>
<div class="form" id="registerForm">
<form method="post" action="/register" onsubmit="return validateRegister()">
<div class="input-group"><label>用户名</label><input type="text" name="username" id="regUser" placeholder="2-20个字符" required minlength="2" maxlength="20" pattern="^[a-zA-Z0-9_]+$"></div>
<div class="input-group"><label>显示名称</label><input type="text" name="display_name" placeholder="选填" maxlength="30"></div>
<div class="input-group"><label>密码</label><input type="password" name="password" id="regPass" placeholder="至少4个字符" required minlength="4"></div>
<button class="btn" type="submit">注册</button>
</form>
<div class="msg" id="regError"></div>
</div>
</div>
<script>
var p=new URLSearchParams(window.location.search);if(p.get('e')==='1')document.getElementById('loginError').style.display='block';if(p.get('reg')==='1'){document.getElementById('loginError').textContent='注册成功，请登录';document.getElementById('loginError').className='msg success';document.getElementById('loginError').style.display='block'}
function switchTab(n){document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});document.querySelectorAll('.form').forEach(function(f){f.classList.remove('active')});if(n==='login'){document.querySelector('.tab:first-child').classList.add('active');document.getElementById('loginForm').classList.add('active')}else{document.querySelector('.tab:last-child').classList.add('active');document.getElementById('registerForm').classList.add('active')}}
function validateRegister(){var p1=document.getElementById('regPass').value;if(p1.length<4){document.getElementById('regError').textContent='密码太短';document.getElementById('regError').style.display='block';return false}return true}
</script></body></html>"""

_ADMIN = """\<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>管理后台 - 茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;display:flex;min-height:100vh}
.sidebar{width:220px;background:#fff;border-right:1px solid #e8e8e8;min-height:100vh;flex-shrink:0;display:flex;flex-direction:column;box-shadow:2px 0 8px rgba(0,0,0,.04)}
.sidebar .logo{padding:20px 16px 12px;font-size:20px;font-weight:700;color:#667eea;text-decoration:none;border-bottom:1px solid #f0f0f0;margin-bottom:8px;white-space:nowrap}
.sidebar .nav-item{padding:12px 20px;cursor:pointer;color:#555;font-size:14px;display:flex;align-items:center;gap:10px;border-left:3px solid transparent;transition:all .2s;margin:2px 0}
.sidebar .nav-item:hover{background:#f5f7ff;color:#667eea}
.sidebar .nav-item.active{background:#f0f2ff;color:#667eea;border-left-color:#667eea;font-weight:500}
.sidebar .nav-item .icon{font-size:18px;width:24px;text-align:center}
.sidebar .nav-spacer{flex:1}
.sidebar .nav-bottom{border-top:1px solid #f0f0f0;padding:12px 20px;font-size:13px;color:#999}
.sidebar .nav-bottom a{color:#999;text-decoration:none}
.sidebar .nav-bottom a:hover{color:#667eea}
.main{flex:1;display:flex;flex-direction:column}
.header{background:#fff;border-bottom:1px solid #e8e8e8;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.header .title{font-size:16px;font-weight:500;color:#333}
.header .user-area{display:flex;align-items:center;gap:16px;font-size:14px;color:#666}
.header .user-area a{color:#e74c3c;text-decoration:none;font-size:13px}
.content{padding:24px;flex:1;overflow-y:auto}
.tab-page{display:none}
.tab-page.active{display:block}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.06);text-align:center}
.stat-card .num{font-size:30px;font-weight:700;color:#667eea}
.stat-card .label{font-size:13px;color:#999;margin-top:4px}
.card{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card h2{font-size:16px;margin-bottom:16px;color:#444}
.user-table{width:100%;border-collapse:collapse;font-size:14px}
.user-table th{text-align:left;padding:10px 12px;border-bottom:2px solid #eee;color:#666;font-weight:500;font-size:13px}
.user-table td{padding:10px 12px;border-bottom:1px solid #f0f0f0;font-size:13px}
.upload-zone{border:2px dashed #ccc;border-radius:10px;padding:36px;text-align:center;cursor:pointer;transition:all .2s}
.upload-zone:hover{border-color:#667eea;background:#f8f9ff}
.upload-icon{font-size:40px;margin-bottom:8px}
progress{width:100%;height:6px;border-radius:3px;margin-top:10px;display:none}
.file-list{list-style:none}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0}
.file-item:last-child{border-bottom:none}
.file-info{flex:1}
.file-name{font-size:14px;font-weight:500}
.file-meta{font-size:12px;color:#999;margin-top:2px}
.file-actions{display:flex;gap:6px}
.file-actions a,.file-actions button{padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer;transition:all .15s}
.file-actions a:hover,.file-actions button:hover{border-color:#667eea;color:#667eea}
.file-actions .del-btn:hover{background:#fff5f5;border-color:#e74c3c;color:#e74c3c}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;z-index:999;transition:opacity .3s}
.toast.show{opacity:1}
.toast.success{background:#27ae60}
.toast.error{background:#e74c3c}
</style></head><body>
<div class="sidebar">
<a href="/" class="logo">茄子数据</a>
<div class="nav-item active" onclick="switchPage('dashboard',this)"><span class="icon">&#x1f4ca;</span>仪表盘</div>
<div class="nav-item" onclick="switchPage('files',this)"><span class="icon">&#x1f4c1;</span>文件管理</div>
<div class="nav-item" onclick="switchPage('upload',this)"><span class="icon">&#x1f4e4;</span>上传</div>
<div class="nav-item" onclick="switchPage('users',this)"><span class="icon">&#x1f465;</span>用户管理</div>
<div class="nav-spacer"></div>
<div class="nav-bottom"><span>&#x1f464; <!--U--></span> &middot; <a href="/logout">退出登录</a></div>
</div>
<div class="main">
<div class="header"><span class="title">管理后台</span><span class="user-area">&#x1f464; <!--U--></span></div>
<div class="content">
<div class="tab-page active" id="page-dashboard">
<div class="stats">
<div class="stat-card"><div class="num" id="statUsers">-</div><div class="label">用户数</div></div>
<div class="stat-card"><div class="num" id="statFiles">-</div><div class="label">文件数</div></div>
<div class="stat-card"><div class="num" id="statSize">-</div><div class="label">存储量</div></div>
<div class="stat-card"><div class="num" id="statAdmin">-</div><div class="label">管理员</div></div>
</div>
</div>
<div class="tab-page" id="page-files">
<div class="card"><h2>全部文件</h2><div id="fileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div class="tab-page" id="page-upload">
<div class="card"><h2>上传文件</h2><div class="upload-zone" id="dropZone"><div class="upload-icon">&#x1f4c1;</div><p style="color:#999">拖拽文件到此处或点击选择</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100"></progress></div>
<div class="card"><h2>我的文件</h2><div id="myFileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div class="tab-page" id="page-users">
<div class="card"><h2>用户列表</h2><table class="user-table"><thead><tr><th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th></tr></thead><tbody id="userTableBody"></tbody></table></div>
</div>
</div></div>
<div id="toast" class="toast"></div>
<script>
function switchPage(id,el){document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});el.classList.add('active');document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('active')});document.getElementById('page-'+id).classList.add('active');if(id==='dashboard')loadDashboard();if(id==='files')loadAllFiles();if(id==='upload')loadMyFiles();if(id==='users')loadUsers()}
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');loadMyFiles()}catch(e){showToast('上传失败','error')}document.getElementById('uploadProgress').style.display='none'}
async function loadDashboard(){try{var r=await fetch('/admin/stats',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();document.getElementById('statUsers').textContent=d.users;document.getElementById('statFiles').textContent=d.files;document.getElementById('statSize').textContent=d.size_display;document.getElementById('statAdmin').textContent=d.admins}catch(e){}}
async function loadAllFiles(){try{var r=await fetch('/admin/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B | '+f.owner+'</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}
async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}
async function loadMyFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('myFileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a><button class=\"del-btn\" onclick=\"delFile('+f.id+')\">删除</button></div></li>'}h+='</ul>';document.getElementById('myFileList').innerHTML=h}catch(e){}}
async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadMyFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}loadDashboard()</script></body></html>"""

_USER = """\<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>我的文件 - 茄子数据</title><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5}
.header{background:#fff;padding:0 24px;height:52px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8e8e8}
.header .logo{font-size:18px;font-weight:700;color:#667eea;text-decoration:none}
.header .user-area{display:flex;align-items:center;gap:12px;font-size:14px;color:#666}
.header .user-area a{color:#e74c3c;text-decoration:none;font-size:13px}
.container{max-width:800px;margin:20px auto;padding:0 16px}
.card{background:#fff;border-radius:10px;padding:20px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.card h2{font-size:16px;margin-bottom:14px;color:#444}
.upload-zone{border:2px dashed #ccc;border-radius:10px;padding:32px;text-align:center;cursor:pointer;transition:all .2s}
.upload-zone:hover{border-color:#667eea;background:#f8f9ff}
.upload-icon{font-size:36px;margin-bottom:6px}
progress{width:100%;height:6px;margin-top:10px;display:none}
.file-list{list-style:none}
.file-item{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f0f0f0}
.file-item:last-child{border-bottom:none}
.file-info{flex:1}
.file-name{font-size:14px;font-weight:500}
.file-meta{font-size:12px;color:#999;margin-top:2px}
.file-actions{display:flex;gap:6px}
.file-actions a,.file-actions button{padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer}
.file-actions a:hover{border-color:#667eea;color:#667eea}
.file-actions button:hover{background:#fff5f5;border-color:#e74c3c;color:#e74c3c}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;z-index:999}
.toast.show{opacity:1}
.toast.success{background:#27ae60}
.toast.error{background:#e74c3c}
</style></head><body>
<div class="header"><a href="/" class="logo">茄子数据</a><div class="user-area"><span>&#x1f464; <!--U--></span><a href="/logout">退出</a></div></div>
<div class="container">
<div class="card"><h2>上传文件</h2><div class="upload-zone" id="dropZone"><div class="upload-icon">&#x1f4c1;</div><p style="color:#999">拖拽文件到此处或点击选择</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100"></progress></div>
<div class="card"><h2>我的文件</h2><div id="fileList"><p style="color:#999;text-align:center;padding:20px">暂无文件</p></div></div>
</div>
<div id="toast" class="toast"></div>
<script>
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');loadFiles()}catch(e){showToast('上传失败','error')}document.getElementById('uploadProgress').style.display='none'}
async function loadFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a><button class=\"del-btn\" onclick=\"delFile('+f.id+')\">删除</button></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}
async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}loadFiles()</script></body></html>"""



if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

