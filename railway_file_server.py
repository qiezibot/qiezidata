# -*- coding: utf-8 -*-
"""
File Manager API - Railway部署版 v2.1
快速修复：模板定义移到底部前 + 延迟赋值
"""
import os, uuid, mimetypes, sqlite3, secrets, hashlib
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse
import asyncio
import functools

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
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL,
                    password_hash VARCHAR(128) NOT NULL, display_name VARCHAR(128),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(), role VARCHAR(16) NOT NULL DEFAULT 'user'
                )
            ''')
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
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS files (
                        id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                        filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL,
                        size BIGINT NOT NULL, mime_type VARCHAR(128),
                        upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL
                    )
                ''')
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, display_name TEXT, created_at TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
        ''')
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL, original_name TEXT NOT NULL,
                    size INTEGER NOT NULL, mime_type TEXT, upload_time TEXT NOT NULL, file_path TEXT NOT NULL
                )
            ''')
        conn.commit(); conn.close()

@app.on_event('startup')
async def startup(): await init_db()

# ===== Database Helpers =====
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

# ===== User System =====
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
    if uid is None: raise HTTPException(status_code=401, detail='not logged in')
    return uid

async def get_user(uid):
    row = await db_fetchrow('SELECT id,username,display_name,role FROM users WHERE id=$1' if use_pg else 'SELECT id,username,display_name,role FROM users WHERE id=?', uid)
    return dict(row) if row else None

# ===== HTML Templates =====
# Must be defined BEFORE if __name__ == '__main__'
LOGIN_HTML = open(os.path.join(os.path.dirname(__file__), 'login.html'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(os.path.dirname(__file__), 'login.html')) else '<html><body><h1>Loading...</h1></body></html>'
ADMIN_HTML_TPL = open(os.path.join(os.path.dirname(__file__), 'admin.html'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(os.path.dirname(__file__), 'admin.html')) else '<html><body><h1>Loading...</h1></body></html>'
USER_HTML_TPL = open(os.path.join(os.path.dirname(__file__), 'user.html'), 'r', encoding='utf-8').read() if os.path.exists(os.path.join(os.path.dirname(__file__), 'user.html')) else '<html><body><h1>Loading...</h1></body></html>'

# === Routes ===

@app.get('/')
async def home(request: Request):
    uid = check_auth(request)
    if uid is None:
        return HTMLResponse(LOGIN_HTML)
    user = await get_user(uid)
    if not user: return HTMLResponse(LOGIN_HTML)
    if user.get('role') == 'admin':
        return HTMLResponse(ADMIN_HTML_TPL.replace('__USERNAME__', user.get('display_name','') or user.get('username','')))
    return HTMLResponse(USER_HTML_TPL.replace('__USERNAME__', user.get('display_name','') or user.get('username','')))

@app.post('/register')
async def register(username: str = Form(...), password: str = Form(...), display_name: str = Form(None)):
    username = username.strip()
    if len(username) < 2 or len(username) > 20:
        return RedirectResponse(url='/?error=reg_invalid', status_code=302)
    existing = await db_fetchrow('SELECT id FROM users WHERE username=$1' if use_pg else 'SELECT id FROM users WHERE username=?', username)
    if existing: return RedirectResponse(url='/?error=reg_exists', status_code=302)
    pw_hash = hash_password(password)
    now = datetime.utcnow().isoformat()
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
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404)
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{fid}')
async def read_file(request: Request, fid: int):
    uid = require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not row: raise HTTPException(status_code=404)
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404)
    text_exts = {'.txt','.json','.xml','.py','.js','.sh','.yaml','.yml','.toml','.sql','.lua','.php','.html','.css','.md','.csv','.ini','.cfg','.conf','.log','.bat','.ps1','.env','.gitignore','.dockerfile','.c','.cpp','.h','.hpp','.java','.go','.rs','.rb','.pl'}
    ext = Path(row['original_name']).suffix.lower()
    if not (row['mime_type'] or '').startswith('text/') and ext not in text_exts:
        raise HTTPException(status_code=400)
    try:
        with open(row['file_path'], 'r', encoding='utf-8') as f: return PlainTextResponse(f.read())
    except UnicodeDecodeError: raise HTTPException(status_code=400)

@app.delete('/delete/{fid}')
async def delete_file(request: Request, fid: int):
    uid = require_auth(request)
    rows = await db_fetch('SELECT * FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'SELECT * FROM files WHERE id=? AND user_id=?', fid, uid)
    if not rows: raise HTTPException(status_code=404)
    row = rows[0]
    if os.path.exists(row['file_path']): os.remove(row['file_path'])
    await db_execute('DELETE FROM files WHERE id=$1 AND user_id=$2' if use_pg else 'DELETE FROM files WHERE id=? AND user_id=?', fid, uid)
    return {'message': 'deleted'}

# Admin routes
@app.get('/admin/stats')
async def admin_stats(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    u = await db_fetchval('SELECT COUNT(*) FROM users' if not use_pg else 'SELECT COUNT(*) FROM users')
    f = await db_fetchval('SELECT COUNT(*) FROM files' if not use_pg else 'SELECT COUNT(*) FROM files')
    s = await db_fetchval('SELECT COALESCE(SUM(size),0) FROM files' if not use_pg else 'SELECT COALESCE(SUM(size),0) FROM files')
    a = await db_fetchval("SELECT COUNT(*) FROM users WHERE role='admin'" if not use_pg else "SELECT COUNT(*) FROM users WHERE role='admin'")
    def fm(b): return f'{b}B' if b<1024 else f'{b/1024:.1f}KB' if b<1024**2 else f'{b/1024**2:.1f}MB' if b<1024**3 else f'{b/1024**3:.1f}GB'
    return {'users': u, 'files': f, 'size': s, 'size_display': fm(s), 'admins': a}

@app.get('/admin/users')
async def admin_users(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch('SELECT id,username,display_name,role,created_at FROM users ORDER BY id' if not use_pg else 'SELECT id,username,display_name,role,created_at FROM users ORDER BY id')
    return [dict(r) for r in rows]

@app.get('/admin/files')
async def admin_files(request: Request):
    uid = require_auth(request)
    user = await get_user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    rows = await db_fetch('SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC' if not use_pg else 'SELECT f.id,f.original_name,f.size,f.upload_time,u.username as owner FROM files f LEFT JOIN users u ON f.user_id=u.id ORDER BY f.upload_time DESC')
    return [{'id': r['id'], 'original_name': r['original_name'], 'size': r['size'],
             'upload_time': str(r['upload_time']) if hasattr(r['upload_time'], 'isoformat') else r['upload_time'],
             'owner': r['owner'] or '?'} for r in rows]

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from starlette.responses import JSONResponse
    status = getattr(exc, 'status_code', 500)
    detail = str(exc.detail) if hasattr(exc, 'detail') else str(exc)
    return JSONResponse(status_code=status, content={'detail': detail})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
