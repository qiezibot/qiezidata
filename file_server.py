"""
File Manager API - 文件上传下载管理服务
FastAPI + SQLite + 异步
"""
import os, shutil, uuid, mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import aiosqlite

# ===== 配置 =====
DB_PATH = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\files.db'
UPLOAD_DIR = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\uploads'
HOST = '0.0.0.0'
PORT = 8899

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager', version='1.0')

# ===== 数据库初始化 =====
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
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
        await db.commit()

@app.on_event('startup')
async def startup():
    await init_db()

# ===== 文件上传 =====
@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    # 生成唯一文件名
    ext = Path(file.filename).suffix if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 保存文件
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    # 写入数据库
    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            'INSERT INTO files (filename, original_name, size, mime_type, upload_time, file_path) VALUES (?, ?, ?, ?, ?, ?)',
            (unique_name, file.filename, len(content), mime, now, file_path)
        )
        await db.commit()
        file_id = cur.lastrowid

    return {
        'id': file_id,
        'filename': file.filename,
        'size': len(content),
        'mime': mime,
        'upload_time': now
    }

# ===== 文件列表 =====
@app.get('/files')
async def list_files():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('SELECT * FROM files ORDER BY upload_time DESC')
        rows = await cur.fetchall()
    return [dict(r) for r in rows]

# ===== 文件下载 =====
@app.get('/download/{file_id}')
async def download_file(file_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')
    if not os.path.exists(row['file_path']):
        raise HTTPException(status_code=404, detail='文件已丢失')

    return FileResponse(
        path=row['file_path'],
        filename=row['original_name'],
        media_type=row['mime_type']
    )

# ===== 读取文件内容（文本文件） =====
@app.get('/read/{file_id}')
async def read_file(file_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')
    if not os.path.exists(row['file_path']):
        raise HTTPException(status_code=404, detail='文件已丢失')

    # 只允许读取文本文件
    text_types = ['text/', 'application/json', 'application/xml', 'application/javascript',
                  'application/x-python', 'application/x-sh', 'application/x-yaml',
                  'application/x-toml', 'application/x-sql', 'application/x-lua',
                  'application/x-httpd-php', 'application/x-www-form-urlencoded']
    mime = row['mime_type']
    ext = Path(row['original_name']).suffix.lower()
    text_exts = {'.txt', '.json', '.xml', '.py', '.js', '.sh', '.yaml', '.yml', '.toml',
                 '.sql', '.lua', '.php', '.html', '.css', '.md', '.csv', '.ini', '.cfg',
                 '.conf', '.log', '.bat', '.ps1', '.env', '.gitignore', '.dockerfile',
                 '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs', '.rb', '.pl', '.r'}

    if not any(mime.startswith(t) for t in text_types) and ext not in text_exts:
        raise HTTPException(status_code=400, detail='不是文本文件，请使用下载接口')

    try:
        with open(row['file_path'], 'r', encoding='utf-8') as f:
            content = f.read()
        return PlainTextResponse(content)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail='不是文本文件，请使用下载接口')

# ===== 删除文件 =====
@app.delete('/delete/{file_id}')
async def delete_file(file_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')

    # 删除物理文件
    if os.path.exists(row['file_path']):
        os.remove(row['file_path'])

    # 删除数据库记录
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM files WHERE id = ?', (file_id,))
        await db.commit()

    return {'message': '删除成功'}

if __name__ == '__main__':
    import uvicorn
    print(f'文件管理服务启动: http://{HOST}:{PORT}')
    uvicorn.run(app, host=HOST, port=PORT)
