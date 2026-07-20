"""
File Manager API - 文件上传下载管理服务 (生产部署版)
FastAPI + MySQL + 文件存储
"""
import os, uuid, mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import aiomysql

# ===== 配置 =====
# 可以通过环境变量覆盖
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', '3306'))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'file_manager')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', '8899'))

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager', version='1.0')

# ===== 数据库连接池 =====
pool = None

async def get_pool():
    global pool
    if pool is None:
        pool = await aiomysql.create_pool(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            db=DB_NAME, autocommit=True,
            minsize=1, maxsize=5
        )
    return pool

async def init_db():
    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255) NOT NULL,
                    size BIGINT NOT NULL,
                    mime_type VARCHAR(128),
                    upload_time DATETIME NOT NULL,
                    file_path VARCHAR(512) NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')

@app.on_event('startup')
async def startup():
    await init_db()

# ===== 文件上传 =====
@app.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix if file.filename else ''
    unique_name = f'{uuid.uuid4().hex}{ext}'
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)

    mime = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    now = datetime.now()

    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                'INSERT INTO files (filename, original_name, size, mime_type, upload_time, file_path) VALUES (%s, %s, %s, %s, %s, %s)',
                (unique_name, file.filename, len(content), mime, now, file_path)
            )
            file_id = cur.lastrowid

    return {
        'id': file_id,
        'filename': file.filename,
        'size': len(content),
        'mime': mime,
        'upload_time': now.isoformat()
    }

# ===== 文件列表 =====
@app.get('/files')
async def list_files():
    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('SELECT id, filename, original_name, size, mime_type, upload_time FROM files ORDER BY upload_time DESC')
            rows = await cur.fetchall()
    # datetime to str
    for r in rows:
        if isinstance(r.get('upload_time'), datetime):
            r['upload_time'] = r['upload_time'].isoformat()
    return rows

# ===== 文件下载 =====
@app.get('/download/{file_id}')
async def download_file(file_id: int):
    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
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
    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
            row = await cur.fetchone()
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
    text_types = ['text/', 'application/json', 'application/xml']

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
    p = await get_pool()
    async with p.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute('SELECT * FROM files WHERE id = %s', (file_id,))
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='文件不存在')

    if os.path.exists(row['file_path']):
        os.remove(row['file_path'])

    async with p.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('DELETE FROM files WHERE id = %s', (file_id,))

    return {'message': '删除成功'}

if __name__ == '__main__':
    import uvicorn
    print(f'文件管理服务启动: http://{HOST}:{PORT}')
    uvicorn.run(app, host=HOST, port=PORT)
