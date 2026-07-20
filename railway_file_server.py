"""
File Manager API - Railway部署版
自动检测数据库：优先PostgreSQL(DATABASE_URL)，否则SQLite
带密码登录保护
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
# 登录密码（通过环境变量设置，默认 admin123）
LOGIN_PASSWORD = os.environ.get('LOGIN_PASSWORD', 'admin123')
# Session密钥
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager (Railway)', version='1.0')

# ===== 数据库层 =====
use_pg = bool(DATABASE_URL)
db_pool = None
db_lock = asyncio.Lock()

async def init_db():
    global db_pool
    if use_pg:
        import asyncpg
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
        async with db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255) NOT NULL,
                    size BIGINT NOT NULL,
                    mime_type VARCHAR(128),
                    upload_time TIMESTAMP NOT NULL DEFAULT NOW(),
                    file_path VARCHAR(512) NOT NULL
                )
            ''')
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                size INTEGER NOT NULL,
                mime_type TEXT,
                upload_time TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

@app.on_event('startup')
async def startup():
    await init_db()

# ===== 数据库辅助 =====
async def db_fetch(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn:
            return await conn.fetch(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        conn.close()
        return rows

async def db_fetchrow(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn:
            return await conn.fetchrow(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        conn.close()
        return row

async def db_execute(sql, *params):
    if use_pg:
        async with db_pool.acquire() as conn:
            return await conn.execute(sql, *params)
    else:
        conn = sqlite3.connect('/data/files.db')
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return row

async def db_insert_returning(sql_insert, sql_params):
    if use_pg:
        return await db_fetchrow(sql_insert, *sql_params)
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql_insert, sql_params)
        row = cur.fetchone()
        conn.commit()
        if not row:
            last_id = cur.lastrowid
            cur = conn.execute('SELECT * FROM files WHERE id = ?', (last_id,))
            row = cur.fetchone()
        conn.close()
        return row

# ===== 登录校验 =====
# Cookie-based simple auth: token = sha256(password + secret_key)
AUTH_COOKIE_NAME = 'qiezidata_token'
AUTH_VALID_TOKENS = set()

def _make_token(pwd: str) -> str:
    return hashlib.sha256(f'{pwd}:{SECRET_KEY}'.encode()).hexdigest()

_valid_token = _make_token(LOGIN_PASSWORD)
AUTH_VALID_TOKENS.add(_valid_token)

def check_auth(request: Request) -> bool:
    token = request.cookies.get(AUTH_COOKIE_NAME, '')
    return token in AUTH_VALID_TOKENS

# ===== HTML 页面 =====

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>登录 - 茄子数据</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}
.login-card {
    background: white;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    max-width: 400px;
    width: 100%;
    text-align: center;
}
.login-card h1 { font-size: 28px; color: #333; margin-bottom: 5px; }
.login-card .subtitle { color: #999; margin-bottom: 30px; font-size: 14px; }
.input-group { margin-bottom: 20px; text-align: left; }
.input-group label { display: block; font-size: 14px; color: #555; margin-bottom: 5px; }
.input-group input {
    width: 100%; padding: 12px 16px; border: 2px solid #eee; border-radius: 8px;
    font-size: 16px; transition: border-color 0.2s; outline: none;
}
.input-group input:focus { border-color: #667eea; }
.btn {
    width: 100%; padding: 12px; background: #667eea; color: white; border: none;
    border-radius: 8px; font-size: 16px; cursor: pointer; transition: background 0.2s;
}
.btn:hover { background: #5a6fd6; }
.error { color: #e74c3c; font-size: 14px; margin-top: 10px; display: none; }
</style>
</head>
<body>
<div class="login-card">
    <h1>🍆 茄子数据</h1>
    <p class="subtitle">文件管理服务</p>
    <form method="post" action="/login">
        <div class="input-group">
            <label>密码</label>
            <input type="password" name="password" placeholder="请输入密码" required autofocus>
        </div>
        <button class="btn" type="submit">登 录</button>
        <div class="error" id="errorMsg">密码错误</div>
    </form>
</div>
<script>
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('error') === '1') {
    document.getElementById('errorMsg').style.display = 'block';
}
</script>
</body>
</html>'''

INDEX_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>茄子数据 - 文件管理</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}
.container { max-width: 800px; margin: 0 auto; }
.card {
    background: white; border-radius: 16px; padding: 30px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2); margin-bottom: 20px;
}
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.top-bar h1 { font-size: 24px; color: #333; margin: 0; }
.top-bar h1 small { font-size: 14px; color: #999; font-weight: normal; }
.top-bar .logout { font-size: 13px; color: #999; text-decoration: none; }
.top-bar .logout:hover { color: #e74c3c; }
.subtitle { color: #666; margin-bottom: 20px; font-size: 14px; }
.upload-zone {
    border: 2px dashed #ccc; border-radius: 12px; padding: 40px 20px;
    text-align: center; cursor: pointer; transition: all 0.3s ease;
}
.upload-zone:hover, .upload-zone.dragover { border-color: #667eea; background: #f8f9ff; }
.upload-zone .icon { font-size: 48px; margin-bottom: 10px; }
.upload-zone p { color: #666; margin-bottom: 5px; }
.upload-zone .hint { font-size: 12px; color: #aaa; }
.file-list { list-style: none; }
.file-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 12px 0; border-bottom: 1px solid #eee;
}
.file-item:last-child { border-bottom: none; }
.file-info { flex: 1; }
.file-name { font-weight: 500; color: #333; word-break: break-all; }
.file-meta { font-size: 12px; color: #999; margin-top: 2px; }
.file-actions { display: flex; gap: 8px; flex-shrink: 0; }
.file-actions a, .file-actions button {
    padding: 6px 12px; font-size: 12px; border: 1px solid #ddd;
    border-radius: 6px; text-decoration: none; color: #555;
    background: #fff; cursor: pointer; transition: all 0.2s;
}
.file-actions a:hover { background: #f0f0f0; }
.file-actions .del-btn:hover { background: #ffeaea; border-color: #e74c3c; color: #e74c3c; }
.empty-state { text-align: center; padding: 40px 20px; color: #999; }
.empty-state .icon { font-size: 48px; margin-bottom: 10px; }
.toast {
    position: fixed; top: 20px; right: 20px; padding: 12px 20px;
    border-radius: 8px; color: white; font-size: 14px;
    opacity: 0; transition: opacity 0.3s; z-index: 999;
}
.toast.show { opacity: 1; }
.toast.success { background: #27ae60; }
.toast.error { background: #e74c3c; }
progress {
    width: 100%; height: 6px; border-radius: 3px; margin-top: 10px; display: none;
}
progress::-webkit-progress-bar { background: #eee; border-radius: 3px; }
progress::-webkit-progress-value { background: #667eea; border-radius: 3px; }
@media (max-width: 600px) {
    .card { padding: 20px; }
    .file-actions { flex-direction: column; gap: 4px; }
}
</style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="top-bar">
            <h1>🍆 茄子数据 <small>v1.0</small></h1>
            <a href="/logout" class="logout">退出登录</a>
        </div>
        <p class="subtitle">文件管理服务 · Railway</p>
        <div class="upload-zone" id="dropZone">
            <div class="icon">📁</div>
            <p>拖拽文件到此处，或点击选择文件</p>
            <p class="hint">支持任意格式，单文件最大 100MB</p>
            <input type="file" id="fileInput" style="display:none">
        </div>
        <progress id="uploadProgress" max="100" value="0"></progress>
        <div id="uploadStatus" style="text-align:center;margin-top:8px;font-size:13px;color:#666;display:none;"></div>
    </div>
    <div class="card">
        <h2 style="font-size:18px;margin-bottom:15px;">📋 文件列表</h2>
        <div id="fileList"><div class="empty-state"><div class="icon">📭</div><p>暂无文件</p></div></div>
    </div>
</div>
<div id="toast" class="toast"></div>
<script>
const API = '';
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const uploadStatus = document.getElementById('uploadStatus');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => { e.preventDefault(); dropZone.classList.remove('dragover'); if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if (fileInput.files.length) uploadFile(fileInput.files[0]); });

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    uploadProgress.style.display = 'block';
    uploadStatus.style.display = 'block';
    uploadStatus.textContent = '上传中: ' + file.name + ' (' + formatSize(file.size) + ')';
    uploadProgress.value = 0;
    try {
        const xhr = new XMLHttpRequest();
        xhr.upload.onprogress = (e) => { if (e.lengthComputable) uploadProgress.value = (e.loaded / e.total) * 100; };
        const result = await new Promise((resolve, reject) => {
            xhr.onload = () => { if (xhr.status === 200) resolve(JSON.parse(xhr.responseText)); else if (xhr.status === 401) { window.location.href='/'; reject('未登录'); } else reject(new Error(xhr.statusText)); };
            xhr.onerror = () => reject(new Error('网络错误'));
            xhr.open('POST', API + '/upload');
            xhr.withCredentials = true;
            xhr.send(formData);
        });
        showToast('上传成功: ' + result.filename, 'success');
        loadFiles();
    } catch (e) { if (e !== '未登录') showToast('上传失败: ' + e.message, 'error'); }
    uploadProgress.style.display = 'none';
    uploadStatus.style.display = 'none';
    fileInput.value = '';
}

async function loadFiles() {
    try {
        const r = await fetch(API + '/files', { credentials: 'include' });
        if (r.status === 401) { window.location.href='/'; return; }
        const files = await r.json();
        const container = document.getElementById('fileList');
        if (files.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文件</p></div>';
            return;
        }
        container.innerHTML = '<ul class="file-list">' + files.map(f => renderFile(f)).join('') + '</ul>';
    } catch (e) { showToast('加载失败', 'error'); }
}

function renderFile(f) {
    const isText = f.mime_type && f.mime_type.startsWith('text/');
    const ext = (f.original_name || '').substring((f.original_name || '').lastIndexOf('.')).toLowerCase();
    const textExts = ['.txt','.json','.xml','.py','.js','.sh','.yaml','.yml','.toml','.sql','.lua','.php','.html','.css','.md','.csv','.ini','.conf','.log','.bat','.ps1','.env','.gitignore','.dockerfile'];
    const canRead = isText || textExts.includes(ext);
    return '<li class="file-item"><div class="file-info"><div class="file-name">' + escapeHtml(f.original_name || f.filename) + '</div><div class="file-meta">' + formatSize(f.size) + ' · ' + f.upload_time + '</div></div><div class="file-actions">' + (canRead ? '<a href="/read/' + f.id + '" target="_blank">📖 查看</a>' : '') + '<a href="/download/' + f.id + '" download>⬇️ 下载</a><button class="del-btn" onclick="deleteFile(' + f.id + ')">🗑️ 删除</button></div></li>';
}

async function deleteFile(id) {
    if (!confirm('确定删除这个文件吗？')) return;
    try {
        const r = await fetch(API + '/delete/' + id, { method: 'DELETE', credentials: 'include' });
        if (r.status === 401) { window.location.href='/'; return; }
        const data = await r.json();
        showToast(data.message || '删除成功', 'success');
        loadFiles();
    } catch (e) { showToast('删除失败', 'error'); }
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/(1024*1024)).toFixed(1) + ' MB';
}
function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function showToast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast ' + type + ' show';
    setTimeout(() => t.classList.remove('show'), 3000);
}
loadFiles();
</script>
</body>
</html>'''

# ===== 路由 =====

@app.get('/')
async def home(request: Request):
    if not check_auth(request):
        return HTMLResponse(LOGIN_HTML)
    return HTMLResponse(INDEX_HTML)

@app.post('/login')
async def login(password: str = Form(...)):
    if password == LOGIN_PASSWORD:
        token = _make_token(password)
        resp = RedirectResponse(url='/', status_code=302)
        resp.set_cookie(key=AUTH_COOKIE_NAME, value=token, httponly=True, max_age=86400*7, samesite='lax')
        return resp
    return RedirectResponse(url='/?error=1', status_code=302)

@app.get('/logout')
async def logout():
    resp = RedirectResponse(url='/', status_code=302)
    resp.delete_cookie(AUTH_COOKIE_NAME)
    return resp

def require_auth(request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401, detail='未登录')

@app.post('/upload')
async def upload_file(request: Request, file: UploadFile = File(...)):
    require_auth(request)
    ext = str(Path(file.filename).suffix) if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    mime = file.content_type or mimetypes.guess_type(str(file.filename))[0] or 'application/octet-stream'
    if use_pg:
        row = await db_insert_returning(
            'INSERT INTO files (filename, original_name, size, mime_type, file_path) VALUES ($1, $2, $3, $4, $5) RETURNING id, upload_time',
            (unique_name, file.filename, len(content), mime, file_path)
        )
        upload_time = row['upload_time'].isoformat()
        fid = row['id']
    else:
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect('/data/files.db')
        conn.execute(
            'INSERT INTO files (filename, original_name, size, mime_type, upload_time, file_path) VALUES (?, ?, ?, ?, ?, ?)',
            (unique_name, file.filename, len(content), mime, now, file_path)
        )
        conn.commit()
        fid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        upload_time = now
    return {'id': fid, 'filename': file.filename, 'size': len(content), 'mime': mime, 'upload_time': upload_time}

@app.get('/files')
async def list_files(request: Request):
    require_auth(request)
    rows = await db_fetch(
        'SELECT id, filename, original_name, size, mime_type, upload_time FROM files ORDER BY upload_time DESC'
    )
    result = []
    for r in rows:
        result.append({
            'id': r['id'], 'filename': r['filename'],
            'original_name': r['original_name'], 'size': r['size'],
            'mime_type': r['mime_type'],
            'upload_time': r['upload_time'] if not use_pg else r['upload_time'].isoformat()
        })
    return result

@app.get('/download/{file_id}')
async def download_file(request: Request, file_id: int):
    require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row: raise HTTPException(status_code=404)
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404, detail='文件已丢失')
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{file_id}')
async def read_file(request: Request, file_id: int):
    require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row: raise HTTPException(status_code=404)
    if not os.path.exists(row['file_path']): raise HTTPException(status_code=404, detail='文件已丢失')
    text_exts = {'.txt', '.json', '.xml', '.py', '.js', '.sh', '.yaml', '.yml', '.toml',
                 '.sql', '.lua', '.php', '.html', '.css', '.md', '.csv', '.ini', '.cfg',
                 '.conf', '.log', '.bat', '.ps1', '.env', '.gitignore', '.dockerfile',
                 '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.rb', '.pl'}
    ext = Path(row['original_name']).suffix.lower()
    mime = row['mime_type']
    if not mime.startswith('text/') and ext not in text_exts:
        raise HTTPException(status_code=400, detail='不是文本文件')
    try:
        with open(row['file_path'], 'r', encoding='utf-8') as f:
            return PlainTextResponse(f.read())
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail='不是文本文件')

@app.delete('/delete/{file_id}')
async def delete_file(request: Request, file_id: int):
    require_auth(request)
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row: raise HTTPException(status_code=404)
    if os.path.exists(row['file_path']): os.remove(row['file_path'])
    await db_execute('DELETE FROM files WHERE id = ?' if not use_pg else 'DELETE FROM files WHERE id = $1', file_id)
    return {'message': '删除成功'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
