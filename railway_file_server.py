"""
File Manager API - Railwayé¨ç½²ç
èªå¨æ£æµæ°æ®åºï¼ä¼åPostgreSQL(DATABASE_URL)ï¼å¦åSQLite
"""
import os, uuid, mimetypes, sqlite3
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
import asyncio

# ===== æ°æ®åºéç½®ï¼èªå¨æ£æµ =====
DATABASE_URL = os.environ.get('DATABASE_URL', '')
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '8000'))

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title='File Manager (Railway)', version='1.0')

# ===== æ°æ®åºå±ï¼èªå¨éæ©ï¼ =====
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

# ===== æ°æ®åºæä½è¾å© =====
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
            # SQLite doesn't support RETURNING, need separate query
            last_id = cur.lastrowid
            cur = conn.execute('SELECT * FROM files WHERE id = ?', (last_id,))
            row = cur.fetchone()
        conn.close()
        return row

# ===== æ¥å£ =====

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
        raise HTTPException(status_code=404, detail='æä»¶å·²ä¸¢å¤±')
    
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
    return {'message': 'å é¤æå'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
