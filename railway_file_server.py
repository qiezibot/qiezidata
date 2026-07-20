# -*- coding: utf-8 -*-
"""
File Manager API - Railway部署版 v2.1
多用户注册/登录 + 管理后台UI
"""
import os, uuid, mimetypes, sqlite3, secrets, hashlib
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse
import asyncio

# ===== 配置 =====
DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

os.makedirs(UPLOAD_DIR, exist_ok=True)
app = FastAPI(title='茄子数据 (Railway)', version='2.1')

# ===== 数据库 =====
use_pg = bool(DATABASE_URL)
db_pool = None

async def init_db():
    global db_pool
    if use_pg:
        import asyncpg
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with db_pool.acquire() as conn:
            await conn.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL, password_hash VARCHAR(128) NOT NULL, display_name VARCHAR(128), created_at TIMESTAMP NOT NULL DEFAULT NOW(), role VARCHAR(16) NOT NULL DEFAULT \'user\')')
            cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='files'")
            col_names = [c['column_name'] for c in cols]
            if 'user_id' not in col_names:
                await conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
                admin = await conn.fetchrow("SELECT id FROM users WHERE username='admin'")
                if not admin:
                    h = hash_password('admin123')
                    await conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)", 'admin', h, '管理员', 'admin')
                    aid = await conn.fetchval("SELECT id FROM users WHERE username='admin'")
                else: aid = admin['id']
                await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)
            if not col_names:
                await conn.execute('CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL, size BIGINT NOT NULL, mime_type VARCHAR(128), upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL)')
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, display_name TEXT, created_at TEXT NOT NULL, role TEXT NOT NULL DEFAULT \'user\')')
        cur = conn.execute("PRAGMA table_info(files)")
        cols = [r[1] for r in cur.fetchall()]
        if 'user_id' not in cols:
            conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
            admin = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
            if not admin:
                h = hash_password('admin123')
                conn.execute("INSERT INTO users (username,password_hash,display_name,created_at,role) VALUES (?,?,?,?,?)",('admin',h,'管理员',datetime.utcnow().isoformat(),'admin'))
                aid = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0]
            else: aid = admin[0]
            conn.execute('UPDATE files SET user_id = ? WHERE user_id IS NULL', (aid,))
        if not cols:
            conn.execute('CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, filename TEXT NOT NULL, original_name TEXT NOT NULL, size INTEGER NOT NULL, mime_type TEXT, upload_time TEXT NOT NULL, file_path TEXT NOT NULL)')
        conn.commit(); conn.close()

@app.on_event('startup')
async def startup(): await init_db()

# ===== 数据库辅助 =====
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
        conn = sqlite3.connect('/data/files.db')
        val = conn.execute(sql, params).fetchone()[0]; conn.close(); return val

# ===== 用户系统 =====
AUTH_COOKIE_NAME = 'qiezidata_token'
def hash_password(pw):
    s = secrets.token_hex(16); return s + ':' + hashlib.sha256((s + pw).encode()).hexdigest()
def verify_password(pw, stored):
    s, h = stored.split(':', 1); return h == hashlib.sha256((s + pw).encode()).hexdigest()
def make_session_token(uid):
    sig = hashlib.sha256(f'{uid}:{SECRET_KEY}'.encode()).hexdigest()[:16]
    return f'{uid}:{sig}'
def parse_session_token(token):
    try:
        parts = token.split(':'); uid = int(parts[0])
        expected = hashlib.sha256(f'{uid}:{SECRET_KEY}'.encode()).hexdigest()[:16]
        return uid if parts[1] == expected else None
    except: return None
def check_auth(request): return parse_session_token(request.cookies.get(AUTH_COOKIE_NAME, ''))
def require_auth(request):
    uid = check_auth(request)
    if uid is None: raise HTTPException(status_code=401, detail='未登录')
    return uid

async def get_user(uid):
    row = await db_fetchrow('SELECT id,username,display_name,role FROM users WHERE id=$1' if use_pg else 'SELECT id,username,display_name,role FROM users WHERE id=?', uid)
    return dict(row) if row else None

# ===== 路由 =====

@app.get('/')
async def home(request: Request):
    uid = check_auth(request)
    if uid is None:
        return HTMLResponse(_LOGIN_HTML)
    user = await get_user(uid)
    if not user: return HTMLResponse(_LOGIN_HTML)
    if user.get('role') == 'admin':
        return HTMLResponse(_ADMIN_HTML_TPL % (user.get('display_name','') or user.get('username','')))
    return HTMLResponse(_USER_HTML_TPL % (user.get('display_name','') or user.get('username','')))

@app.post('/register')
async def register(username: str = Form(...), password: str = Form(...), display_name: str = Form(None)):
    username = username.strip()
    if len(username) < 2 or len(username) > 20:
        return RedirectResponse(url='/?error=reg_invalid', status_code=302)
    existing = await db_fetchrow('SELECT id FROM users WHERE username=$1' if use_pg else 'SELECT id FROM users WHERE username=?', username)
    if existing: return RedirectResponse(url='/?error=reg_exists', status_code=302)
    pw_hash = hash_password(password); now = datetime.utcnow().isoformat()
    if use_pg:
        await db_execute('INSERT INTO users (username,password_hash,display_name) VALUES ($1,$2,$3)', username, pw_hash, display_name or username)
    else:
        await db_execute('INSERT INTO users (username,password_hash,display_name,created_at) VALUES (?,?,?,?)', username, pw_hash, display_name or username, now)
    return RedirectResponse(url='/?registered=1', status_code=302)

@app.post('/login')
async def login(username: str = Form(...), password: str = Form(...)):
    row = await db_fetchrow('SELECT id,password_hash FROM users WHERE username=$1' if use_pg else 'SELECT id,password_hash FROM users WHERE username=?', username.strip())
    if not row or not verify_password(password, row['password_hash']):
        return RedirectResponse(url='/?error=1', status_code=302)
    token = make_session_token(row['id'])
    resp = RedirectResponse(url='/', status_code=302)
    resp.set_cookie(key=AUTH_COOKIE_NAME, value=token, httponly=True, max_age=86400*7, samesite='lax')
    return resp

@app.get('/logout')
async def logout():
    resp = RedirectResponse(url='/', status_code=302)
    resp.delete_cookie(AUTH_COOKIE_NAME)
    return resp

@app.get('/me')
async def get_me(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user: raise HTTPException(status_code=404)
    return user

@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    uid = require_auth(request)
    ext = str(Path(file.filename).suffix) if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    user_dir = os.path.join(UPLOAD_DIR, str(uid))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, unique_name)
    content = await file.read()
    with open(file_path, 'wb') as f: f.write(content)
    mime = file.content_type or mimetypes.guess_type(str(file.filename))[0] or 'application/octet-stream'
    if use_pg:
        row = await db_fetchrow('INSERT INTO files (user_id,filename,original_name,size,mime_type,file_path) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id,upload_time', uid, unique_name, file.filename, len(content), mime, file_path)
        fid, upt = row['id'], row['upload_time'].isoformat()
    else:
        now = datetime.utcnow().isoformat()
        cur = await db_execute('INSERT INTO files (user_id,filename,original_name,size,mime_type,upload_time,file_path) VALUES (?,?,?,?,?,?,?)', uid, unique_name, file.filename, len(content), mime, now, file_path)
        fid, upt = cur.lastrowid, now
    return {'id': fid, 'filename': file.filename, 'size': len(content), 'mime': mime, 'upload_time': upt}

@app.get('/files')
async def list_files(request: Request):
    uid = require_auth(request)
    rows = await db_fetch('SELECT id,filename,original_name,size,mime_type,upload_time FROM files WHERE user_id=$1 ORDER BY upload_time DESC' if use_pg else 'SELECT id,filename,original_name,size,mime_type,upload_time FROM files WHERE user_id=? ORDER BY upload_time DESC', uid)
    return [{**dict(r), 'upload_time': r['upload_time'] if not use_pg else r['upload_time'].isoformat()} for r in rows]

@app.get('/download/{fid}')
async def download_file(request: Request, fid: int):
    uid = require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not row: raise HTTPException(status_code=404)
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404, detail='文件已丢失')
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{fid}')
async def read_file(request: Request, fid: int):
    uid = require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not row: raise HTTPException(status_code=404)
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404, detail='文件已丢失')
    text_exts = {'.txt','.json','.xml','.py','.js','.sh','.yaml','.yml','.toml','.sql','.lua','.php','.html','.css','.md','.csv','.ini','.cfg','.conf','.log','.bat','.ps1','.env','.gitignore','.dockerfile','.c','.cpp','.h','.hpp','.java','.go','.rs','.rb','.pl'}
    ext = Path(row['original_name']).suffix.lower()
    if not (row['mime_type'] or '').startswith('text/') and ext not in text_exts:
        raise HTTPException(status_code=400, detail='不是文本文件')
    try:
        with open(row['file_path'], 'r', encoding='utf-8') as f: return PlainTextResponse(f.read())
    except UnicodeDecodeError: raise HTTPException(status_code=400, detail='不是文本文件')

@app.delete('/delete/{fid}')
async def delete_file(request: Request, fid: int):
    uid = require_auth(request)
    rows = await db_fetch('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not rows: raise HTTPException(status_code=404)
    row = rows[0]
    if os.path.exists(row['file_path']): os.remove(row['file_path'])
    await db_execute('DELETE FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'DELETE FROM files WHERE id=? AND user_id=?', fid, uid)
    return {'message': '删除成功'}

# ---- 管理员路由 ----
@app.get('/admin/stats')
async def admin_stats(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403, detail='需要管理员权限')
    users = await db_fetchval('SELECT COUNT(*) FROM users' if not use_pg else 'SELECT COUNT(*) FROM users')
    files = await db_fetchval('SELECT COUNT(*) FROM files' if not use_pg else 'SELECT COUNT(*) FROM files')
    total_size = await db_fetchval('SELECT COALESCE(SUM(size),0) FROM files' if not use_pg else 'SELECT COALESCE(SUM(size),0) FROM files')
    admins = await db_fetchval("SELECT COUNT(*) FROM users WHERE role='admin'" if not use_pg else "SELECT COUNT(*) FROM users WHERE role='admin'")
    def fmt(b): return f'{b}B' if b<1024 else f'{b/1024:.1f}KB' if b<1024**2 else f'{b/1024**2:.1f}MB' if b<1024**3 else f'{b/1024**3:.1f}GB'
    return {'users': users, 'files': files, 'size': total_size, 'size_display': fmt(total_size), 'admins': admins}

@app.get('/admin/users')
async def admin_users(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch('SELECT id,username,display_name,role,created_at FROM users ORDER BY id' if not use_pg else 'SELECT id,username,display_name,role,created_at FROM users ORDER BY id')
    return [{'id': r['id'], 'username': r['username'], 'display_name': r['display_name'], 'role': r['role'],
             'created_at': str(r['created_at']) if hasattr(r['created_at'], 'isoformat') else r['created_at']} for r in rows]

@app.get('/admin/files')
async def admin_files(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch('SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC' if not use_pg else 'SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC')
    return [{'id': r['id'], 'original_name': r['original_name'], 'size': r['size'],
             'upload_time': str(r['upload_time']) if hasattr(r['upload_time'], 'isoformat') else r['upload_time'],
             'owner': r['owner'] or '?'} for r in rows]

# ===== Exception Handler =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from starlette.responses import JSONResponse
    status = getattr(exc, 'status_code', 500)
    detail = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
    return JSONResponse(status_code=status, content={'detail': detail})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)

# ===== HTML Templates (plain strings, not f-strings) =====

LOGIN_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(255,255,255,.95);border-radius:20px;padding:45px 40px;box-shadow:0 20px 60px rgba(0,0,0,.3);max-width:420px;width:100%;text-align:center;backdrop-filter:blur(10px)}
.card h1{font-size:32px;color:#333;margin-bottom:5px}.card .subtitle{color:#999;margin-bottom:30px;font-size:14px}
.tabs{display:flex;margin-bottom:28px;border-bottom:2px solid #eee}.tab{flex:1;text-align:center;padding:12px;cursor:pointer;color:#999;font-weight:500;transition:.2s;border-bottom:2px solid transparent;margin-bottom:-2px}
.tab.active{color:#667eea;border-bottom-color:#667eea}.tab:hover{color:#667eea}
.form{display:none}.form.active{display:block}.input-group{margin-bottom:18px;text-align:left}.input-group label{display:block;font-size:13px;color:#555;margin-bottom:5px;font-weight:500}
.input-group input{width:100%;padding:12px 14px;border:2px solid #eee;border-radius:10px;font-size:15px;transition:.2s;outline:none}
.input-group input:focus{border-color:#667eea}
.btn{width:100%;padding:12px;background:#667eea;color:#fff;border:none;border-radius:10px;font-size:16px;cursor:pointer;transition:.2s;font-weight:500}
.btn:hover{background:#5a6fd6}.msg{font-size:13px;margin-top:10px;display:none;padding:8px 12px;border-radius:6px}
.msg.error{display:block;color:#c0392b;background:#fdecea}.msg.success{display:block;color:#27ae60;background:#eafaf1}
</style></head><body>
<div class="card"><h1>馃崋 茄子数据</h1><p class="subtitle">文件管理服务 v2.1</p>
<div class="tabs"><div class="tab active" onclick="switchTab('login')">登录</div><div class="tab" onclick="switchTab('register')">注册</div></div>
<div class="form active" id="loginForm"><form method="post" action="/login"><div class="input-group"><label>用户名</label><input type="text" name="username" placeholder="输入用户名" required autofocus></div><div class="input-group"><label>密码</label><input type="password" name="password" placeholder="输入密码" required></div><button class="btn" type="submit">登 录</button></form><div class="msg error" id="loginError">用户名或密码错误</div></div>
<div class="form" id="registerForm"><form method="post" action="/register" onsubmit="return validateRegister()"><div class="input-group"><label>用户名</label><input type="text" name="username" id="regUser" placeholder="2-20位字母数字" required minlength="2" maxlength="20" pattern="^[a-zA-Z0-9_]+$"></div><div class="input-group"><label>显示名称（可选）</label><input type="text" name="display_name" id="regDisplay" placeholder="别人看到的名字" maxlength="30"></div><div class="input-group"><label>密码</label><input type="password" name="password" id="regPass" placeholder="至少4位" required minlength="4"></div><div class="input-group"><label>确认密码</label><input type="password" name="password2" id="regPass2" placeholder="再次输入" required></div><button class="btn" type="submit">注 册</button></form><div class="msg error" id="regError"></div></div></div>
<script>
const p=new URLSearchParams(window.location.search);if(p.get('error')==='1')document.getElementById('loginError').style.display='block'
if(p.get('registered')==='1'){switchTab('login');document.getElementById('loginError').textContent='注册成功，请登录';document.getElementById('loginError').className='msg success';document.getElementById('loginError').style.display='block'}
function switchTab(n){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.form').forEach(f=>f.classList.remove('active'));if(n==='login'){document.querySelector('.tab:first-child').classList.add('active');document.getElementById('loginForm').classList.add('active')}else{document.querySelector('.tab:last-child').classList.add('active');document.getElementById('registerForm').classList.add('active')}}
function validateRegister(){var p1=document.getElementById('regPass').value,p2=document.getElementById('regPass2').value,err=document.getElementById('regError');if(p1!==p2){err.textContent='两次密码不一致';err.className='msg error';err.style.display='block';return false}return true}
</script></body></html>"""

ADMIN_HTML_TPL = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据 - 管理后台</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;min-height:100vh;color:#333}
.header{background:#fff;border-bottom:1px solid #e8e8e8;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 4px rgba(0,0,0,.05)}
.header .logo{font-size:20px;font-weight:700;color:#667eea;text-decoration:none;display:flex;align-items:center;gap:8px}
.header .user-area{display:flex;align-items:center;gap:16px;font-size:14px}.header .user-area a{color:#999;text-decoration:none;cursor:pointer}.header .user-area a:hover{color:#e74c3c}
.layout{display:flex;min-height:calc(100vh-56px)}.sidebar{width:200px;background:#fff;border-right:1px solid #e8e8e8;padding:16px 0;flex-shrink:0}
.sidebar .nav-item{padding:12px 24px;cursor:pointer;display:flex;align-items:center;gap:10px;color:#555;font-size:14px;transition:.15s;border-left:3px solid transparent;text-decoration:none}
.sidebar .nav-item:hover{background:#f5f7ff;color:#667eea}.sidebar .nav-item.active{background:#f0f2ff;color:#667eea;border-left-color:#667eea;font-weight:500}
.main{flex:1;padding:24px;max-width:1200px}
.card{background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}.card h2{font-size:18px;margin-bottom:16px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,.06);text-align:center}
.stat-card .num{font-size:32px;font-weight:700;color:#667eea;margin-bottom:4px}.stat-card .label{font-size:13px;color:#999}
.tab-page{display:none}.tab-page.active{display:block}
.upload-zone{border:2px dashed #ccc;border-radius:12px;padding:40px 20px;text-align:center;cursor:pointer;transition:.3s}
.upload-zone:hover,.upload-zone.dragover{border-color:#667eea;background:#f8f9ff}.upload-zone .icon{font-size:48px;margin-bottom:10px}.upload-zone .hint{font-size:12px;color:#aaa}
.file-list{list-style:none}.file-item{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid #f0f0f0}.file-item:last-child{border-bottom:none}
.file-info{flex:1}.file-name{font-weight:500;color:#333;word-break:break-all}.file-meta{font-size:12px;color:#999;margin-top:2px}
.file-actions{display:flex;gap:6px;flex-shrink:0}
.file-actions a,.file-actions button{padding:5px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer;transition:.15s}
.file-actions a:hover{background:#f0f0f0}.file-actions .del-btn:hover{background:#ffeaea;border-color:#e74c3c;color:#e74c3c}
.empty-state{text-align:center;padding:40px 20px;color:#999}.empty-state .icon{font-size:48px;margin-bottom:10px}
progress{width:100%;height:6px;border-radius:3px;margin-top:10px;display:none}progress::-webkit-progress-bar{background:#eee;border-radius:3px}progress::-webkit-progress-value{background:#667eea;border-radius:3px}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;transition:.3s;z-index:999}.toast.show{opacity:1}.toast.success{background:#27ae60}.toast.error{background:#e74c3c}
.user-table{width:100%;border-collapse:collapse;font-size:14px}
.user-table th{text-align:left;padding:10px 12px;border-bottom:2px solid #eee;color:#666;font-weight:500}
.user-table td{padding:10px 12px;border-bottom:1px solid #f0f0f0}.user-table tr:hover td{background:#fafafa}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:500}
.badge-admin{background:#e8f4fd;color:#2196f3}.badge-user{background:#f0f0f0;color:#666}
</style></head><body>
<div class="header"><a href="/" class="logo">馃崋 茄子数据</a><div class="user-area"><span>馃懁 %s</span><span class="badge badge-admin">管理员</span><a href="/logout">退出</a></div></div>
<div class="layout"><div class="sidebar">
<a class="nav-item active" onclick="switchPage('dashboard',this)">馃搳 概览</a>
<a class="nav-item" onclick="switchPage('files',this)">馃搧 文件管理</a>
<a class="nav-item" onclick="switchPage('upload',this)">馃摛 上传文件</a>
<a class="nav-item" onclick="switchPage('users',this)">馃懃 用户管理</a>
<a class="nav-item" onclick="switchPage('about',this)">ℹ️ 关于</a>
</div><div class="main">
<div class="tab-page active" id="page-dashboard"><div class="stats"><div class="stat-card"><div class="num" id="statUsers">-</div><div class="label">用户总数</div></div><div class="stat-card"><div class="num" id="statFiles">-</div><div class="label">文件总数</div></div><div class="stat-card"><div class="num" id="statSize">-</div><div class="label">总容量</div></div><div class="stat-card"><div class="num" id="statAdmin">-</div><div class="label">管理员</div></div></div></div>
<div class="tab-page" id="page-files"><div class="card"><h2>馃搵 所有用户文件</h2><div id="fileList"><div class="empty-state"><div class="icon">馃摥</div><p>暂无文件</p></div></div></div></div>
<div class="tab-page" id="page-upload"><div class="card"><h2>馃摛 上传文件</h2><div class="upload-zone" id="dropZone"><div class="icon">馃搧</div><p>拖拽文件到此处，或点击选择文件</p><p class="hint">支持任意格式，单文件最大 100MB</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100" value="0"></progress><div id="uploadStatus" style="display:none"></div><div style="margin-top:16px"><h3 style="font-size:15px;margin-bottom:10px">我的文件</h3><div id="myFileList"><div class="empty-state"><p>暂无文件</p></div></div></div></div></div>
<div class="tab-page" id="page-users"><div class="card"><h2>馃懃 用户管理</h2><table class="user-table"><thead><tr><th>ID</th><th>用户名</th><th>显示名</th><th>角色</th><th>注册时间</th></tr></thead><tbody id="userTableBody"></tbody></table></div></div>
<div class="tab-page" id="page-about"><div class="card"><h2>ℹ️ 关于</h2><p style="line-height:1.8;color:#666;font-size:14px">馃崋 茄子数据 v2.1<br>基于 FastAPI + PostgreSQL 构建<br>多用户文件管理系统<br><br>馃搶 默认管理员: admin / admin123<br>馃敀 每个用户文件隔离</p></div></div>
</div></div>
<div id="toast" class="toast"></div>
<script>
function switchPage(id,el){document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});el.classList.add('active');document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('active')});document.getElementById('page-'+id).classList.add('active');if(id==='dashboard')loadDashboard();if(id==='files')loadAllFiles();if(id==='users')loadUsers();if(id==='upload')loadMyFiles()}
var API='';
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});
document.getElementById('dropZone').addEventListener('dragover',function(e){e.preventDefault();document.getElementById('dropZone').classList.add('dragover')});
document.getElementById('dropZone').addEventListener('dragleave',function(){document.getElementById('dropZone').classList.remove('dragover')});
document.getElementById('dropZone').addEventListener('drop',function(e){e.preventDefault();document.getElementById('dropZone').classList.remove('dragover');if(e.dataTransfer.files.length)uploadFile(e.dataTransfer.files[0])});
document.getElementById('fileInput').addEventListener('change',function(){if(document.getElementById('fileInput').files.length)uploadFile(document.getElementById('fileInput').files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);var p=document.getElementById('uploadProgress'),s=document.getElementById('uploadStatus');p.style.display='block';s.style.display='block';s.textContent='上传中: '+file.name;var xhr=new XMLHttpRequest();xhr.upload.onprogress=function(e){if(e.lengthComputable)p.value=(e.loaded/e.total)*100};try{var r=await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve(JSON.parse(xhr.responseText));else if(xhr.status===401)window.location.href='/';else reject(new Error(xhr.statusText))};xhr.onerror=function(){reject(new Error('网络错误'))};xhr.open('POST',API+'/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功: '+r.filename,'success');loadMyFiles()}catch(e){showToast('上传ʧ败','error')}
p.style.display='none';s.style.display='none';document.getElementById('fileInput').value=''}
async function loadDashboard(){try{var r=await fetch(API+'/admin/stats',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();document.getElementById('statUsers').textContent=d.users;document.getElementById('statFiles').textContent=d.files;document.getElementById('statSize').textContent=d.size_display;document.getElementById('statAdmin').textContent=d.admins}catch(e){}}
async function loadAllFiles(){try{var r=await fetch(API+'/admin/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();var el=document.getElementById('fileList');if(!files.length){el.innerHTML='<div class="empty-state"><div class="icon">??</div><p>暂无文件</p></div>';return}
el.innerHTML='<ul class="file-list">'+files.map(function(f){return '<li class="file-item"><div class="file-info"><div class="file-name">'+esc(f.original_name)+'</div><div class="file-meta">'+fmtSize(f.size)+' 用户: '+esc(f.owner)+' '+f.upload_time+'</div></div><div class="file-actions"><a href="/download/'+f.id+'" download>??</a><button class="del-btn" onclick="delAdminFile('+f.id+')">???</button></div></li>'}).join('')+'</ul>'}catch(e){}}
async function delAdminFile(id){if(!confirm('ȷ定ɾ除？'))return;try{var r=await fetch(API+'/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('ɾ除成功','success');loadAllFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
async function loadUsers(){try{var r=await fetch(API+'/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();document.getElementById('userTableBody').innerHTML=users.map(function(u){return '<tr><td>'+u.id+'</td><td>'+esc(u.username)+'</td><td>'+esc(u.display_name||'-')+'</td><td><span class="badge '+(u.role==='admin'?'badge-admin':'badge-user')+'">'+u.role+'</span></td><td>'+u.created_at+'</td></tr>'}).join('')}catch(e){}}
async function loadMyFiles(){try{var r=await fetch(API+'/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();var el=document.getElementById('myFileList');if(!files.length){el.innerHTML='<div class="empty-state"><p>暂无文件</p></div>';return}
el.innerHTML='<ul class="file-list">'+files.map(function(f){var te=['.txt','.json','.xml','.py','.js','.sh','.yaml','.toml','.sql','.html','.css','.md','.csv','.log','.bat','.ps1'];var ext='.'+(f.original_name||'').split('.').pop();var cr=f.mime_type&&f.mime_type.startsWith('text/')||te.includes(ext);return '<li class="file-item"><div class="file-info"><div class="file-name">'+esc(f.original_name)+'</div><div class="file-meta">'+fmtSize(f.size)+' '+f.upload_time+'</div></div><div class="file-actions">'+(cr?'<a href="/read/'+f.id+'" target="_blank">??</a>':'')+'<a href="/download/'+f.id+'" download>??</a><button class="del-btn" onclick="delMyFile('+f.id+')">???</button></div></li>'}).join('')+'</ul>'}catch(e){}}
async function delMyFile(id){if(!confirm('ȷ定ɾ除？'))return;try{var r=await fetch(API+'/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('ɾ除成功','success');loadMyFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
function fmtSize(b){if(b<1024)return b+'B';if(b<1024*1024)return (b/1024).toFixed(1)+'KB';return (b/(1024*1024)).toFixed(1)+'MB'}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}
loadDashboard();
</script></body></html>"""

USER_HTML_TPL = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据 - 我的文件</title>
<style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;min-height:100vh;color:#333}
.header{background:#fff;border-bottom:1px solid #e8e8e8;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.header .logo{font-size:20px;font-weight:700;color:#667eea;text-decoration:none}.header .user-area{display:flex;align-items:center;gap:16px;font-size:14px;color:#666}
.header .user-area a{color:#999;text-decoration:none;cursor:pointer}.header .user-area a:hover{color:#e74c3c}
.container{max-width:900px;margin:24px auto;padding:0 20px}
.card{background:#fff;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}.card h2{font-size:18px;margin-bottom:16px}
.upload-zone{border:2px dashed #ccc;border-radius:12px;padding:40px;text-align:center;cursor:pointer;transition:.3s}
.upload-zone:hover,.upload-zone.dragover{border-color:#667eea;background:#f8f9ff}.upload-zone .icon{font-size:48px}.upload-zone .hint{font-size:12px;color:#aaa}
.file-list{list-style:none}.file-item{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f0f0f0}.file-item:last-child{border-bottom:none}
.file-info{flex:1}.file-name{font-weight:500}.file-meta{font-size:12px;color:#999}
.file-actions{display:flex;gap:6px}.file-actions a,.file-actions button{padding:5px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;text-decoration:none;color:#555;background:#fff;cursor:pointer}
.file-actions .del-btn:hover{background:#ffeaea;border-color:#e74c3c;color:#e74c3c}
.empty-state{text-align:center;padding:40px;color:#999}
progress{width:100%;height:6px;border-radius:3px;margin-top:10px;display:none}progress::-webkit-progress-bar{background:#eee}progress::-webkit-progress-value{background:#667eea;border-radius:3px}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;color:#fff;font-size:14px;opacity:0;transition:.3s;z-index:999}.toast.show{opacity:1}.toast.success{background:#27ae60}.toast.error{background:#e74c3c}
</style></head><body>
<div class="header"><div><a href="/" class="logo">?? 茄子数据</a></div><div class="user-area"><span>?? %s</span><a href="/logout">退出</a></div></div>
<div class="container">
<div class="card"><h2>?? 上传文件</h2><div class="upload-zone" id="dropZone"><div class="icon">??</div><p>拖ק文件或点击ѡ择</p><p class="hint">֧持任意格ʽ</p><input type="file" id="fileInput" style="display:none"></div><progress id="uploadProgress" max="100" value="0"></progress><div id="uploadStatus" style="display:none"></div></div>
<div class="card"><h2>?? 我的文件</h2><div id="fileList"><div class="empty-state"><p>暂无文件</p></div></div></div></div>
<div id="toast" class="toast"></div>
<script>
var API='';
document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});
document.getElementById('dropZone').addEventListener('dragover',function(e){e.preventDefault();document.getElementById('dropZone').classList.add('dragover')});
document.getElementById('dropZone').addEventListener('dragleave',function(){document.getElementById('dropZone').classList.remove('dragover')});
document.getElementById('dropZone').addEventListener('drop',function(e){e.preventDefault();document.getElementById('dropZone').classList.remove('dragover');if(e.dataTransfer.files.length)uploadFile(e.dataTransfer.files[0])});
document.getElementById('fileInput').addEventListener('change',function(){if(document.getElementById('fileInput').files.length)uploadFile(document.getElementById('fileInput').files[0])});
async function uploadFile(file){var fd=new FormData();fd.append('file',file);var p=document.getElementById('uploadProgress'),s=document.getElementById('uploadStatus');p.style.display='block';s.style.display='block';s.textContent='上传中: '+file.name;var xhr=new XMLHttpRequest();xhr.upload.onprogress=function(e){if(e.lengthComputable)p.value=(e.loaded/e.total)*100};try{var r=await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve(JSON.parse(xhr.responseText));else if(xhr.status===401)window.location.href='/';else reject(new Error(xhr.statusText))};xhr.onerror=function(){reject(new Error('网络错误'))};xhr.open('POST',API+'/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功: '+r.filename,'success');loadFiles()}catch(e){showToast('上传ʧ败','error')}
p.style.display='none';s.style.display='none';document.getElementById('fileInput').value=''}
async function loadFiles(){try{var r=await fetch(API+'/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();var el=document.getElementById('fileList');if(!files.length){el.innerHTML='<div class="empty-state"><p>暂无文件</p></div>';return}
el.innerHTML='<ul class="file-list">'+files.map(function(f){var te=['.txt','.json','.xml','.py','.js','.sh','.yaml','.toml','.sql','.html','.css','.md','.csv','.log','.bat','.ps1'];var ext='.'+(f.original_name||'').split('.').pop();var cr=f.mime_type&&f.mime_type.startsWith('text/')||te.includes(ext);return '<li class="file-item"><div class="file-info"><div class="file-name">'+esc(f.original_name)+'</div><div class="file-meta">'+fmtSize(f.size)+' '+f.upload_time+'</div></div><div class="file-actions">'+(cr?'<a href="/read/'+f.id+'" target="_blank">??</a>':'')+'<a href="/download/'+f.id+'" download>??</a><button class="del-btn" onclick="delFile('+f.id+')">???</button></div></li>'}).join('')+'</ul>'}catch(e){}}
async function delFile(id){if(!confirm('ȷ定ɾ除？'))return;try{var r=await fetch(API+'/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('ɾ除成功','success');loadFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}
function fmtSize(b){if(b<1024)return b+'B';if(b<1024*1024)return (b/1024).toFixed(1)+'KB';return (b/(1024*1024)).toFixed(1)+'MB'}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function showToast(m,t){var el=document.getElementById('toast');el.textContent=m;el.className='toast '+t+' show';setTimeout(function(){el.classList.remove('show')},3000)}
loadFiles();
</script></body></html>"""



# ===== Template References (defined above) =====
_LOGIN_HTML = LOGIN_HTML
_ADMIN_HTML_TPL = ADMIN_HTML_TPL
_USER_HTML_TPL = USER_HTML_TPL
