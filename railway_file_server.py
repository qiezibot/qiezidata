"""
File Manager API - Railway部署版
使用Railway内置PostgreSQL
"""
import os, uuid, mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import asyncpg

# ===== Railway 自动注入的数据库地址 =====
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/filemgr')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))  # Railway默认8000

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager (Railway)', version='1.0')

# ===== 数据库连接池 =====
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return pool

async def init_db():
    p = await get_pool()
    async with p.acquire() as conn:
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

@app.on_event('startup')
async def startup():
    await init_db()

# ===== 接口 =====

@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    p = await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow(
            'INSERT INTO files (filename, original_name, size, mime_type, file_path) VALUES ($1, $2, $3, $4, $5) RETURNING id, upload_time',
            unique_name, file.filename, len(content), mime, file_path
        )

    return {
        'id': row['id'],
        'filename': file.filename,
        'size': len(content),
        'mime': mime,
        'upload_time': row['upload_time'].isoformat()
    }

@app.get('/files')
async def list_files():
    p = await get_pool()
    async with p.acquire() as conn:
        rows = await conn.fetch('SELECT id, filename, original_name, size, mime_type, upload_time FROM files ORDER BY upload_time DESC')
    result = []
    for r in rows:
        result.append({
            'id': r['id'],
            'filename': r['filename'],
            'original_name': r['original_name'],
            'size': r['size'],
            'mime_type': r['mime_type'],
            'upload_time': r['upload_time'].isoformat()
        })
    return result

@app.get('/download/{file_id}')
async def download_file(file_id: int):
    p = await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')
    if not os.path.exists(row['file_path']):
        raise HTTPException(status_code=404, detail='文件已丢失')
    return FileResponse(path=row['file_path'], filename=row['original_name'], media_type=row['mime_type'])

@app.get('/read/{file_id}')
async def read_file(file_id: int):
    p = await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')
    if not os.path.exists(row['file_path']):
        raise HTTPException(status_code=404, detail='文件已丢失')

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
async def delete_file(file_id: int):
    p = await get_pool()
    async with p.acquire() as conn:
        row = await conn.fetchrow('SELECT * FROM files WHERE id = $1', file_id)
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')
    if os.path.exists(row['file_path']):
        os.remove(row['file_path'])
    await conn.execute('DELETE FROM files WHERE id = $1', file_id)
    return {'message': '删除成功'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
