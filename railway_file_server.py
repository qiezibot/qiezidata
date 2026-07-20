"""
<<<<<<< HEAD
File Manager API - Railwayé¨ç½²ç
èªå¨æ£æµæ°æ®åºï¼ä¼åPostgreSQL(DATABASE_URL)ï¼å¦åSQLite
=======
File Manager API - Railway部署版
自动检测数据库：优先PostgreSQL(DATABASE_URL)，否则SQLite
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
"""
import os, uuid, mimetypes, sqlite3
from datetime import datetime
from pathlib import Path
<<<<<<< HEAD
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import asyncio

# ===== æ°æ®åºéç½®ï¼èªå¨æ£æµ =====
=======
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
import asyncio

# ===== 数据库配置：自动检测 =====
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager (Railway)', version='1.0')

<<<<<<< HEAD
# ===== æ°æ®åºå±ï¼èªå¨éæ©ï¼ =====
=======
# ===== 数据库层（自动选择） =====
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
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
        # SQLite fallback
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

<<<<<<< HEAD
# ===== æ°æ®åºæä½è¾å© =====
=======
# ===== 数据库操作辅助 =====
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
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

async def db_fetchval(sql, *params):
    if use_pg:
        return await db_fetchrow(sql, *params)
    else:
        return await db_fetchrow(sql, *params)

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
<<<<<<< HEAD
            # SQLite doesn't support RETURNING, need separate query
=======
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
            last_id = cur.lastrowid
            cur = conn.execute('SELECT * FROM files WHERE id = ?', (last_id,))
            row = cur.fetchone()
        conn.close()
        return row

<<<<<<< HEAD
# ===== æ¥å£ =====
=======
# ===== 前端页面 =====

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
.container {
    max-width: 800px;
    margin: 0 auto;
}
.card {
    background: white;
    border-radius: 16px;
    padding: 30px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    margin-bottom: 20px;
}
h1 {
    font-size: 24px;
    color: #333;
    margin-bottom: 5px;
}
h1 small {
    font-size: 14px;
    color: #999;
    font-weight: normal;
}
.subtitle {
    color: #666;
    margin-bottom: 20px;
    font-size: 14px;
}
.upload-zone {
    border: 2px dashed #ccc;
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
}
.upload-zone:hover, .upload-zone.dragover {
    border-color: #667eea;
    background: #f8f9ff;
}
.upload-zone .icon {
    font-size: 48px;
    margin-bottom: 10px;
}
.upload-zone p {
    color: #666;
    margin-bottom: 5px;
}
.upload-zone .hint {
    font-size: 12px;
    color: #aaa;
}
.btn {
    display: inline-block;
    padding: 10px 24px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}
.btn:hover { background: #5a6fd6; }
.btn:disabled { background: #ccc; cursor: not-allowed; }
.btn-danger { background: #e74c3c; }
.btn-danger:hover { background: #c0392b; }
.file-list { list-style: none; }
.file-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #eee;
}
.file-item:last-child { border-bottom: none; }
.file-info { flex: 1; }
.file-name {
    font-weight: 500;
    color: #333;
    word-break: break-all;
}
.file-meta {
    font-size: 12px;
    color: #999;
    margin-top: 2px;
}
.file-actions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
}
.file-actions a, .file-actions button {
    padding: 6px 12px;
    font-size: 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    text-decoration: none;
    color: #555;
    background: #fff;
    cursor: pointer;
    transition: all 0.2s;
}
.file-actions a:hover { background: #f0f0f0; }
.file-actions .del-btn:hover { background: #ffeaea; border-color: #e74c3c; color: #e74c3c; }
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #999;
}
.empty-state .icon { font-size: 48px; margin-bottom: 10px; }
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-size: 14px;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: 999;
}
.toast.show { opacity: 1; }
.toast.success { background: #27ae60; }
.toast.error { background: #e74c3c; }
progress {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    margin-top: 10px;
    display: none;
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
        <h1>🍆 茄子数据 <small>v1.0</small></h1>
        <p class="subtitle">文件管理服务 · <span id="server-info">Railway</span></p>
        
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
            xhr.onload = () => { if (xhr.status === 200) resolve(JSON.parse(xhr.responseText)); else reject(new Error(xhr.statusText)); };
            xhr.onerror = () => reject(new Error('网络错误'));
            xhr.open('POST', API + '/upload');
            xhr.send(formData);
        });
        showToast('上传成功: ' + result.filename, 'success');
        loadFiles();
    } catch (e) {
        showToast('上传失败: ' + e.message, 'error');
    }
    uploadProgress.style.display = 'none';
    uploadStatus.style.display = 'none';
    fileInput.value = '';
}

async function loadFiles() {
    try {
        const r = await fetch(API + '/files');
        const files = await r.json();
        const container = document.getElementById('fileList');
        if (files.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>暂无文件</p></div>';
            return;
        }
        container.innerHTML = '<ul class="file-list">' + files.map(f => renderFile(f)).join('') + '</ul>';
    } catch (e) {
        showToast('加载文件列表失败', 'error');
    }
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
        const r = await fetch(API + '/delete/' + id, { method: 'DELETE' });
        const data = await r.json();
        showToast(data.message || '删除成功', 'success');
        loadFiles();
    } catch (e) {
        showToast('删除失败', 'error');
    }
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
    return (bytes/(1024*1024)).toFixed(1) + ' MB';
}

function escapeHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function showToast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + type + ' show';
    setTimeout(() => t.classList.remove('show'), 3000);
}

loadFiles();
</script>
</body>
</html>'''

# ===== 接口 =====
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)

@app.get('/')
async def index():
    return HTMLResponse(INDEX_HTML)

@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    
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
    
    return {
        'id': fid,
        'filename': file.filename,
        'size': len(content),
        'mime': mime,
        'upload_time': upload_time
    }

@app.get('/files')
async def list_files():
    rows = await db_fetch(
        'SELECT id, filename, original_name, size, mime_type, upload_time FROM files ORDER BY upload_time DESC'
    )
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'filename': r['filename'],
            'original_name': r['original_name'],
            'size': r['size'],
            'mime_type': r['mime_type'],
            'upload_time': r['upload_time'] if not use_pg else r['upload_time'].isoformat()
        })
    return result

@app.get('/download/{file_id}')
async def download_file(file_id: int):
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='æä»¶ä¸å­å¨')
    if not os.path.exists(row['file_path']):
        raise HTTPException(status_code=404, detail='æä»¶å·²ä¸¢å¤±')
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{file_id}')
async def read_file(file_id: int):
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='æä»¶ä¸å­å¨')
    if not os.path.exists(row['file_path']):
<<<<<<< HEAD
        raise HTTPException(status_code=404, detail='æä»¶å·²ä¸¢å¤±')
=======
        raise HTTPException(status_code=404, detail='文件已丢失')
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)
    
    text_exts = {'.txt', '.json', '.xml', '.py', '.js', '.sh', '.yaml', '.yml', '.toml',
                 '.sql', '.lua', '.php', '.html', '.css', '.md', '.csv', '.ini', '.cfg',
                 '.conf', '.log', '.bat', '.ps1', '.env', '.gitignore', '.dockerfile',
                 '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.rb', '.pl'}
    ext = Path(row['original_name']).suffix.lower()
    mime = row['mime_type']
    if not mime.startswith('text/') and ext not in text_exts:
        raise HTTPException(status_code=400, detail='ä¸æ¯ææ¬æä»¶')
    try:
        with open(row['file_path'], 'r', encoding='utf-8') as f:
            return PlainTextResponse(f.read())
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail='ä¸æ¯ææ¬æä»¶')

@app.delete('/delete/{file_id}')
async def delete_file(file_id: int):
    row = await db_fetchrow('SELECT * FROM files WHERE id = ?' if not use_pg else 'SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='æä»¶ä¸å­å¨')
    if os.path.exists(row['file_path']):
        os.remove(row['file_path'])
    await db_execute('DELETE FROM files WHERE id = ?' if not use_pg else 'DELETE FROM files WHERE id = $1', file_id)
<<<<<<< HEAD
    return {'message': 'å é¤æå'}
=======
    return {'message': '删除成功'}
>>>>>>> f354c6a (add web UI: upload page with drag-drop, file list, download, read, delete)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
