# -*- coding: utf-8 -*-



"""



Fil



            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id SERIAL PRIMARY KEY,name VARCHAR(255) NOT NULL,token VARCHAR(64) NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')



            # migrate old clouddata to default project



            try:



                cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata_projects")



                if cnt == 0:



                    await conn.execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", 'default', 'token_default')



                    old_cd = await conn.fetchval("SELECT COUNT(*) FROM clouddata")



                    if old_cd > 0:



                        await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects WHERE name='default') WHERE project_id IS NULL")



            except: pass



            try:



                await conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER REFERENCES clouddata_projects(id) DEFAULT 1")



                await conn.execute("ALTER TABLE clouddata ADD COLUMN name VARCHAR(255) DEFAULT ''")



                await conn.execute("ALTER TABLE clouddata ADD COLUMN md5 VARCHAR(32) DEFAULT ''")



            except: pass



e Manager - Eggplant Data v2.1



Multi-user + Admin Dashboard + File Management



"""



import os, uuid, mimetypes, sqlite3, secrets, hashlib



from datetime import datetime



from pathlib import Path



from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, Body



from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse, Response, JSONResponse







DATABASE_URL = os.environ.get('DATABASE_URL', '')



UPLOAD_DIR = os.environ.get('UPLOAD_DIR', '/data/uploads')



HOST = '0.0.0.0'



PORT = int(os.environ.get('PORT', '8000'))



SECRET_KEY = os.environ.get('SECRET_KEY', 'c3adc9837be6a1ad025450a8568e77bb19d3db42221875e2afa7d98c4706af2a')



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



            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata(id SERIAL PRIMARY KEY,k VARCHAR(255) UNIQUE NOT NULL,v TEXT NOT NULL,t TIMESTAMP DEFAULT CURRENT_TIMESTAMP,read BOOLEAN NOT NULL DEFAULT FALSE)')



            # clouddata column migration



            try:



                cdcols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name=$1", 'clouddata')



                if 'read' not in [c['column_name'] for c in cdcols]:



                    await conn.execute("ALTER TABLE clouddata ADD COLUMN read BOOLEAN NOT NULL DEFAULT FALSE")



            except: pass







            await conn.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username VARCHAR(64) UNIQUE NOT NULL, password_hash VARCHAR(128) NOT NULL, display_name VARCHAR(128), created_at TIMESTAMP NOT NULL DEFAULT NOW(), role VARCHAR(16) NOT NULL DEFAULT \'user\')')



            # 迁移：给旧 users 表添加 role 列



            ucols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='users'")



            if 'role' not in [c['column_name'] for c in ucols]:



                await conn.execute("ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'user'")



            try:



                cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='files'")



            except:



                cols = []



            if not cols:



                await conn.execute('CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL, size BIGINT NOT NULL, mime_type VARCHAR(128), upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL)')



            else:



                if 'user_id' not in [c['column_name'] for c in cols]:



                    await conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')



                    admin = await conn.fetchrow("SELECT id FROM users WHERE username='admin'")



                    if not admin:



                        h = _hash('admin123')



                        await conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)", 'admin', h, 'Admin', 'admin')



                        aid = await conn.fetchval("SELECT id FROM users WHERE username='admin'")



                    else: aid = admin['id']



                    await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)



            # clouddata_projects



            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id SERIAL PRIMARY KEY,name VARCHAR(255) NOT NULL,token VARCHAR(64) NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')



            try:



                await conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER REFERENCES clouddata_projects(id) DEFAULT 1")



                await conn.execute("ALTER TABLE clouddata ADD COLUMN name VARCHAR(255) DEFAULT ''")



                await conn.execute("ALTER TABLE clouddata ADD COLUMN md5 VARCHAR(32) DEFAULT ''")



            except: pass



            try:



                cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata_projects")



                if cnt == 0:



                    await conn.execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", 'default', 'default_token')



                    old_cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata")



                    if old_cnt > 0:



                        await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects WHERE name='default')")



                await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects LIMIT 1) WHERE project_id IS NULL")



            except: pass







    else:



        conn = sqlite3.connect('/data/files.db')



        conn.execute('CREATE TABLE IF NOT EXISTS clouddata(id INTEGER PRIMARY KEY AUTOINCREMENT,k TEXT UNIQUE NOT NULL,v TEXT NOT NULL,t TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0)')



        conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,token TEXT NOT NULL,created_at TEXT NOT NULL)')



        try: conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER DEFAULT 1")



        except: pass



        try: conn.execute("ALTER TABLE clouddata ADD COLUMN name TEXT DEFAULT ''")



        except: pass



        try: conn.execute("ALTER TABLE clouddata ADD COLUMN md5 TEXT DEFAULT ''")



        except: pass







        try: conn.execute('ALTER TABLE clouddata ADD COLUMN read INTEGER NOT NULL DEFAULT 0')



        except: pass







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











@app.post('/admin/user/{uid}/set_admin')

async def set_user_admin(uid: int, request: Request):

    admin_id = _require(request); admin_user = await _user(admin_id)

    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT id FROM users WHERE id=$1', uid)

            if not row:

                return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)

            await conn.execute('UPDATE users SET role=\'admin\' WHERE id=$1', uid)

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT id FROM users WHERE id=?', (uid,))

        if not cur.fetchone():

            conn.close()

            return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)

        cur.execute('UPDATE users SET role=\'admin\' WHERE id=?', (uid,))

        conn.commit(); conn.close()

    return JSONResponse({'ok':True})



@app.post('/admin/user/{uid}/unset_admin')

async def unset_user_admin(uid: int, request: Request):

    admin_id = _require(request); admin_user = await _user(admin_id)

    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)

    if admin_id == uid:
        return JSONResponse({'ok':False,'detail':'不能取消自己的管理员'}, status_code=400)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT id FROM users WHERE id=$1', uid)

            if not row:
                return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)

            await conn.execute('UPDATE users SET role=\'user\' WHERE id=$1', uid)

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT id FROM users WHERE id=?', (uid,))

        if not cur.fetchone():
            conn.close()
            return JSONResponse({'ok':False,'detail':'user not found'}, status_code=404)

        cur.execute('UPDATE users SET role=\'user\' WHERE id=?', (uid,))

        conn.commit(); conn.close()

    return JSONResponse({'ok':True,'detail':'已取消管理员'})



@app.post('/admin/user/{uid}/set_id')



async def set_user_id(uid: int, new_id: int = Body(...), request: Request = None):



    if not request:



        return JSONResponse({'ok': False, 'detail': '无权限'}, status_code=403)



    admin_uid = _require(request)



    async with db_pool.acquire() as conn:



        # Check if admin



        row = await conn.fetchrow('SELECT role FROM users WHERE id=$1', admin_uid)



        if not row or row['role'] != 'admin':



            return JSONResponse({'ok': False, 'detail': '无权限'}, status_code=403)



        # Check target user exists



        target = await conn.fetchrow('SELECT id, username FROM users WHERE id=$1', uid)



        if not target:



            return JSONResponse({'ok': False, 'detail': '用户不存在'}, status_code=404)



        # Bypass FK: tmp user -> move tmp -> swap user -> update files -> cleanup



        await conn.execute("INSERT INTO users (id, username, display_name, role, password_hash, created_at) VALUES (" + str(new_id) + ", '~tmp~', '~tmp~', 'user', '', NOW()) ON CONFLICT DO NOTHING")



        await conn.execute("UPDATE users SET id=0 WHERE id=" + str(new_id) + " AND username='~tmp~'")



        await conn.execute('UPDATE users SET id=$1 WHERE id=$2', new_id, uid)



        await conn.execute('UPDATE files SET user_id=$1 WHERE user_id=$2', new_id, uid)



        await conn.execute("DELETE FROM users WHERE id=0 AND username='~tmp~'")



        return JSONResponse({'ok': True, 'msg': f'用户ID {uid} 已改为 {new_id}'})











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



        return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))



    return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))







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



    resp.set_cookie(key=AUTH_COOKIE, value=token, httponly=True, max_age=86400*7, samesite='lax', secure=True)



    return resp







@app.get('/logout')



async def logout():



    resp = RedirectResponse(url='/', status_code=302)



    resp.delete_cookie(AUTH_COOKIE)



    return resp







@app.get('/me')



async def get_me(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user: raise HTTPException(status_code=404)



    return user










@app.post('/me')
async def update_me(request: Request):
    uid = _require(request)
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'ok': False, 'detail': '请求格式错误'})
    dn = data.get('display_name', '')
    if dn:
        if use_pg:
            await db_execute('UPDATE users SET display_name=$1 WHERE id=$2', dn, uid)
        else:
            await db_execute('UPDATE users SET display_name=? WHERE id=?', dn, uid)
    return JSONResponse({'ok': True})

@app.post('/me/change_password')
async def change_my_password(request: Request):
    uid = _require(request)
    data = await request.json()
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not new_pw or len(new_pw) < 4:
        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})
    if use_pg:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=$1', uid)
        if not row or row['password_hash'] != _hash(old_pw):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=?', uid)
        if not row or row['password_hash'] != _hash(old_pw):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=? WHERE id=?', _hash(new_pw), uid)
    return JSONResponse({'ok': True})

@app.post('/admin/user/{uid}/change_password')
async def admin_change_user_password(uid: int, request: Request):
    aid = _require(request)
    admin_user = await _user(aid)
    if not admin_user or admin_user.get('role') != 'admin':
        raise HTTPException(status_code=403)
    data = await request.json()
    new_pw = data.get('new_password', '')
    if not new_pw or len(new_pw) < 4:
        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})
    if use_pg:
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        await db_execute('UPDATE users SET password_hash=? WHERE id=?', _hash(new_pw), uid)
    return JSONResponse({'ok': True})

@app.post('/me')
async def update_me(request: Request):
    uid = _require(request)
    data = await request.json()
    dn = data.get('display_name', '')
    if dn:
        if use_pg:
            await db_execute('UPDATE users SET display_name=$1 WHERE id=$2', dn, uid)
        else:
            await db_execute('UPDATE users SET display_name=? WHERE id=?', dn, uid)
    return JSONResponse({'ok': True})
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







@app.get('/clouddata/export/{mode}')



async def script_cd_export(mode: str, request: Request):



    _require(request)



    if mode == 'all':



        r = await db_fetch('SELECT k,v,t,read FROM clouddata ORDER BY id' if use_pg else 'SELECT k,v,t,read FROM clouddata ORDER BY id')



    elif mode == 'read':



        r = await db_fetch('SELECT k,v,t,read FROM clouddata WHERE read=true ORDER BY id' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE read=1 ORDER BY id')



    elif mode == 'unread':



        r = await db_fetch('SELECT k,v,t,read FROM clouddata WHERE read=false ORDER BY id' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE read=0 ORDER BY id')



    else:



        raise HTTPException(400, 'mode must be all/read/unread')



    import io, csv



    buf = io.StringIO(); w = csv.writer(buf)



    w.writerow(['Key','Value','Time','Read'])



    for x in r:



        t = str(x['t']) if x['t'] else ''



        red = 'Yes' if x['read'] else 'No'



        w.writerow([x['k'], x['v'], t, red])



    csv_content = buf.getvalue(); buf.close()



    from datetime import datetime



    fname = 'clouddata_%s_%s.csv' % (mode, datetime.utcnow().strftime('%Y%m%d_%H%M%S'))



    return Response(content=csv_content, media_type='text/csv',



        headers={'Content-Disposition': 'attachment; filename=' + fname})







@app.post('/clouddata/mark/{key}')



async def script_cd_mark(key: str, request: Request, read: bool = True):



    _require(request)



    if use_pg:



        await db_execute('UPDATE clouddata SET read=$1 WHERE k=$2', read, key)



    else:



        await db_execute('UPDATE clouddata SET read=? WHERE k=?', 1 if read else 0, key)



    return {'ok': True, 'key': key, 'read': read}







@app.post('/clouddata/mark/id/{cid}')



async def script_cd_mark_id(cid: int, request: Request, read: bool = True):



    _require(request)



    if use_pg:



        await db_execute('UPDATE clouddata SET read=$1 WHERE id=$2', read, cid)



    else:



        await db_execute('UPDATE clouddata SET read=? WHERE id=?', 1 if read else 0, cid)



    return {'ok': True, 'id': cid, 'read': read}















@app.post('/clouddata')



async def script_cd_upsert(request: Request):



    uid = _require(request)



    b = await request.json(); k = b.get('数据名称','').strip(); v = b.get('数据','').strip()



    if not k or not v: raise HTTPException(400)



    if use_pg:



        await db_execute('INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2', k, v)



    else:



        await db_execute('INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)', k, v)



    return {'ok': True, 'key': k, 'value': v}







@app.get('/clouddata')



async def script_cd_list(request: Request, key: str = None):



    _require(request)



    if key:



        r = await db_fetchrow('SELECT k,v,t,read FROM clouddata WHERE k=$1' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE k=?', key)



        if r:



            return {'key':r['k'],'value':r['v'],'time':str(r['t']),'read':r['read']}



        return {'error':'not found'}



    r = await db_fetch('SELECT k,v,t,read FROM clouddata ORDER BY id DESC' if use_pg else 'SELECT k,v,t,read FROM clouddata ORDER BY id DESC')



    return [{'key':x['k'],'value':x['v'],'time':str(x['t']) if x['t'] else '','read':x['read']} for x in r]







@app.get('/clouddata/{key}')



async def script_cd_get(key: str, request: Request):



    _require(request)



    r = await db_fetchrow('SELECT k,v,t,read FROM clouddata WHERE k=$1' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE k=?', key)



    if not r: raise HTTPException(404, 'key not found')



    return {'key':r['k'],'value':r['v'],'time':str(r['t']),'read':r['read']}







@app.delete('/clouddata/{key}')



async def script_cd_delete(key: str, request: Request):



    _require(request)



    if use_pg:



        await db_execute('DELETE FROM clouddata WHERE k=$1', key)



    else:



        await db_execute('DELETE FROM clouddata WHERE k=?', key)



    return {'ok': True, 'key': key}







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







@app.delete('/admin/file/{fid}')



async def admin_delete_file(request: Request, fid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin':



        raise HTTPException(status_code=403)



    row = await db_fetchrow('SELECT * FROM files WHERE id=$1' if use_pg else 'SELECT * FROM files WHERE id=?', fid)



    if not row:



        raise HTTPException(status_code=404)



    if os.path.exists(row['file_path']):



        os.remove(row['file_path'])



    await db_execute('DELETE FROM files WHERE id=$1' if use_pg else 'DELETE FROM files WHERE id=?', fid)



    return {'ok': True, 'msg': '\u6587\u4ef6\u5df2\u5220\u9664'}







@app.get('/admin/clouddata')



async def clouddata_list(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        return await db_fetch("SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata ORDER BY id DESC")



    else:



        return await db_fetch('SELECT id,k,v,t,read FROM clouddata ORDER BY id DESC')







@app.post('/admin/clouddata/add')



async def clouddata_add(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    b = await request.json(); k = b.get('数据名称','').strip(); v = b.get('数据','').strip(); pid = b.get('project_id')



    if not k or not v: raise HTTPException(400)



    if pid is not None:



        import hashlib



        name = k; md5 = hashlib.md5(v.encode()).hexdigest()



        if use_pg:



            await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND k=$2", pid, k)



            await db_execute("INSERT INTO clouddata(project_id,k,v,name,md5) VALUES($1,$2,$3,$4,$5)", pid, k, v, name, md5)



        else:



            await db_execute("DELETE FROM clouddata WHERE project_id=? AND k=?", pid, k)



            await db_execute("INSERT INTO clouddata(project_id,k,v,name,md5) VALUES(?,?,?,?,?)", pid, k, v, name, md5)



    else:



        if use_pg:



            await db_execute('INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2', k, v)



        else:



            await db_execute('INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)', k, v)



    return {'ok': True}







@app.delete('/admin/clouddata/{cid}')



async def clouddata_del(cid: int, request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        await db_execute('DELETE FROM clouddata WHERE id=$1', cid)



    else:



        await db_execute('DELETE FROM clouddata WHERE id=?', cid)



    return {'ok': True}







@app.get('/admin/stats')



async def admin_stats(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    u = await db_fetchval('SELECT COUNT(*) FROM users' if not use_pg else 'SELECT COUNT(*) FROM users')



    f = await db_fetchval('SELECT COUNT(*) FROM files' if not use_pg else 'SELECT COUNT(*) FROM files')



    s = await db_fetchval("SELECT COALESCE(SUM(size),0) FROM files" if not use_pg else "SELECT COALESCE(SUM(size),0) FROM files")



    a = await db_fetchval("SELECT COUNT(*) FROM users WHERE role='admin'" if not use_pg else "SELECT COUNT(*) FROM users WHERE role='admin'")



    def fm(b): return f'{b}B' if b<1024 else f'{b/1024:.1f}KB' if b<1024**2 else f'{b/1024**2:.1f}MB'



    return {'users': u, 'files': f, 'size': s, 'size_display': fm(s), 'admins': a}







@app.get('/admin/users')



async def admin_users(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    rows = await db_fetch('SELECT id,username,display_name,role,created_at FROM users ORDER BY id' if not use_pg else 'SELECT id,username,display_name,role,created_at FROM users ORDER BY id')



    return [dict(r) for r in rows]







@app.delete('/admin/user/{uid}')



async def admin_delete_user(uid: int, request: Request):



    aid = _require(request); admin_user = await _user(aid)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if uid == aid: raise HTTPException(status_code=400, detail='不能删除自己')



    target = await _user(uid)



    if not target: raise HTTPException(status_code=404, detail='用户不存在')



    # 删除该用户的文件



    rows = await db_fetch('SELECT file_path FROM files WHERE user_id=$1' if use_pg else 'SELECT file_path FROM files WHERE user_id=?', uid)



    for row in rows:



        fp = row['file_path']



        if os.path.exists(fp): os.remove(fp)



    await db_execute('DELETE FROM files WHERE user_id=$1' if use_pg else 'DELETE FROM files WHERE user_id=?', uid)



    # 删除用户



    await db_execute('DELETE FROM users WHERE id=$1' if use_pg else 'DELETE FROM users WHERE id=?', uid)



    return {'ok': True, 'msg': f'用户 {target["username"]} 已删除'}







@app.get('/admin/files')



async def admin_files(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



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



_LOGIN = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>茄子数据</title><style>



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

.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);z-index:9999;justify-content:center;align-items:center}
.modal-content{background:#fff;border-radius:12px;padding:24px 28px;max-width:380px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.2);animation:modalIn .25s ease}
.modal-close{float:right;font-size:22px;cursor:pointer;color:#999;line-height:1}.modal-close:hover{color:#333}
.modal h3{margin:0 0 12px;font-size:16px;color:#333}
.modal h4{margin:12px 0 8px;font-size:14px;color:#555}
.form-group{margin-bottom:10px}.form-group label{display:block;font-size:12px;color:#666;margin-bottom:3px}
.form-group input{width:100%;padding:8px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px;outline:none;box-sizing:border-box}
.form-group input:focus{border-color:#7c5cfc;box-shadow:0 0 0 2px rgba(124,92,252,0.15)}
.modal .btn{background:linear-gradient(135deg,#7c5cfc,#5a3fd6);color:#fff;border:none;padding:8px 20px;border-radius:6px;font-size:13px;cursor:pointer;width:auto;margin-top:4px}
.modal .btn:hover{background:linear-gradient(135deg,#8b6dff,#6b51e6)}
.modal .msg{font-size:12px;padding:6px 10px;margin-top:8px}
@keyframes modalIn{from{opacity:0;transform:scale(.92) translateY(-10px)}to{opacity:1;transform:scale(1) translateY(0)}}



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



</script><script>
(function(){var r=document.body.dataset.role||'';if(r!='admin'){document.querySelectorAll('.nav-item').forEach(function(n){if(n.getAttribute('onclick')&&n.getAttribute('onclick').indexOf('users')>=0)n.style.display='none'});}})();
</script>
</body></html>"""







_ADMIN = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>管理后台 - 茄子数据</title><style>



*{margin:0;padding:0;box-sizing:border-box}



body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;display:flex;min-height:100vh}



.sidebar{width:220px;background:#fff;border-right:1px solid #e8e8e8;min-height:100vh;flex-shrink:0;display:flex;flex-direction:column}



.sidebar .logo{padding:20px 16px 12px;font-size:20px;font-weight:700;color:#667eea;border-bottom:1px solid #f0f0f0;margin-bottom:8px}



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





.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);z-index:9999;justify-content:center;align-items:center}
.modal-content{background:#fff;border-radius:12px;padding:24px 28px;max-width:380px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.2);animation:modalIn .25s ease}
.modal-close{float:right;font-size:22px;cursor:pointer;color:#999;line-height:1}.modal-close:hover{color:#333}
.modal h3{margin:0 0 12px;font-size:16px;color:#333}
.modal h4{margin:12px 0 8px;font-size:14px;color:#555}
.modal .btn{background:linear-gradient(135deg,#7c5cfc,#5a3fd6);color:#fff;border:none;padding:8px 20px;border-radius:6px;font-size:13px;cursor:pointer;width:auto;margin-top:4px}
.modal .btn:hover{background:linear-gradient(135deg,#8b6dff,#6b51e6)}
.modal .msg{font-size:12px;padding:6px 10px;margin-top:8px}
@keyframes modalIn{from{opacity:0;transform:scale(.92) translateY(-10px)}to{opacity:1;transform:scale(1) translateY(0)}}

</style></head><body>
<!-- 个人资料弹窗 -->
<div id="profileModal" class="modal" style="display:none"><div class="modal-content" style="max-width:420px"><span class="modal-close" onclick="closeProfile()">&times;</span><h3>个人资料</h3><div class="form-group"><label>用户名</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><div class="form-group"><label>显示名称</label><input id="profModalDN" type="text" placeholder="输入显示名称"></div><div class="form-group"><label>角色</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><button class="btn" onclick="saveProfileModal()">保存</button><div id="profModalSaveMsg" class="msg" style="display:none"></div><hr style="margin:16px 0"><h4>修改密码</h4><div class="form-group"><label>旧密码</label><input id="profModalOldPwd" type="password" placeholder="输入旧密码"></div><div class="form-group"><label>新密码</label><input id="profModalNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认新密码</label><input id="profModalNewPwd2" type="password" placeholder="再次输入"></div><button class="btn" onclick="submitProfilePwdModal()">修改密码</button><div id="profModalPwdMsg" class="msg" style="display:none"></div></div></div>
<!-- 管理员改用户密码 -->
<div id="changePasswordModal" class="modal" style="display:none"><div class="modal-content" style="max-width:380px"><span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span><h3>修改用户密码</h3><p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p><div class="form-group"><label>新密码</label><input id="cpNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认密码</label><input id="cpConfirmPwd" type="password" placeholder="再次输入新密码"></div><button class="btn" onclick="submitAdminChangePwd()">确认修改</button><div id="cpMsg" class="msg" style="display:none"></div></div></div>






<div class="sidebar">



<span class="logo">茄子数据</span>



<div class="nav-item active" onclick="switchPage('dashboard',this)"><span class="icon">&#x1f4ca;</span>仪表盘</div>



<div class="nav-item" onclick="switchPage('files',this)"><span class="icon">&#x1f4c1;</span>文件管理</div>



<div class="nav-item" onclick="switchPage('upload',this)"><span class="icon">&#x1f4e4;</span>上传</div>



<div class="nav-item" onclick="switchPage('users',this)"><span class="icon">&#x1f465;</span>用户管理</div>



<div class="nav-item" onclick="switchPage('clouddata',this)"><span class="icon">&#x2601;</span>云数据</div>



<div class="nav-item" onclick="switchPage('apidocs',this)"><span class="icon">📖</span>API文档</div>



<div class="nav-spacer"></div>



<div class="nav-bottom"><span>&#x1f464; <!--U--></span> &middot; <a href="/logout">退出登录</a></div>



</div>



<div class="main">



<div class="header"><span class="title">管理后台</span><span class="user-area">&#x1f464; <!--U--> | <a href="javascript:void(0)" onclick="openProfileModal()">个人资料</a></span></div>



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



<div class="card"><h2>用户列表</h2><table class="user-table"><thead><tr><th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th></tr><th style="width:100px">密码</th></thead><tbody id="userTableBody"></tbody></table></div>



</div>



<div class="tab-page" id="page-clouddata">



<div class="card" style="background:#edf7ec;padding:10px">



<div style="margin-bottom:10px">



<span style="font-size:18px">选择数据名称:</span>



<select id="cdpSelect" style="width:300px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc"></select>



<button onclick="createProject()" class="btn btn-info" style="margin:0 5px">创建云数据项目</button>



<button onclick="deleteProject()" class="btn btn-danger">删除当前选择项目</button>



<button onclick="resetAllRead(document.getElementById('cdpSelect').value)" class="btn btn-success" style="margin:0 5px">设置全部数据状态为未读取</button>



</div>



<div style="margin-bottom:10px">



<span style="font-size:16px">总数:</span><span id="cdTotal" style="font-size:17px;font-weight:bold">0</span>



<span style="font-size:16px;margin-left:15px">未读取:</span><span id="cdNoRead" style="font-size:17px;font-weight:bold;color:orange">0</span>



<span style="font-size:16px;margin-left:15px">已读取:</span><span id="cdRead" style="font-size:17px;font-weight:bold;color:green">0</span>



<button onclick="loadCloudDataStats(document.getElementById('cdpSelect').value)" class="btn btn-info" style="margin-left:10px">刷新</button>



</div>



<div style="overflow:auto">



<table class="user-table" style="font-size:13px">



<thead><tr><th>项目ID</th><th>项目名称</th><th>访问Token</th><th>项目创建时间</th><th>操作命令</th></tr><th style="width:100px">密码</th></thead>



<tbody id="cdpTableBody"></tbody>



</table>



</div>



</div>







<h5 style="margin:1px"></h5>



<div class="card" style="background:#fff4f4;padding:10px">



<div style="margin-bottom:10px">



<span style="font-size:18px">选择数据状态:</span>



<select id="cdQueryType" style="width:200px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc">



<option value="-1">所有数据</option>



<option value="0">未读取的数据</option>



<option value="1">已读取的数据</option>



</select>



<button onclick="exportCD('all')" class="btn btn-success">导出所有数据</button>



<button onclick="exportCD('unread')" class="btn btn-success">导出所有未读取数据</button>



<button onclick="exportCD('read')" class="btn btn-success">导出所有已读取数据</button>



<div class="btn-group" style="display:inline-block;margin-left:5px">



<button class="btn btn-danger dropdown-toggle" onclick="var m=this.nextElementSibling;m.style.display=m.style.display=='none'?'block':'none'">删除数据 &#9660;</button>



<ul style="display:none;position:absolute;background:#fff;border:1px solid #ccc;list-style:none;padding:5px;z-index:10">



<li><a href="#" onclick="batchDelete('all');return false" style="color:#333">删除所有数据</a></li>



<li><a href="#" onclick="batchDelete('read');return false" style="color:#333">删除所有已读取数据</a></li>



<li><a href="#" onclick="batchDelete('unread');return false" style="color:#333">删除所有未读取数据</a></li>



</ul>



</div>



<input id="cdSearchText" type="text" style="width:300px;display:inline-block;padding:4px;border-radius:4px;border:1px solid #ccc;margin-left:10px" placeholder="输入数据名字搜索数据" onkeydown="if(event.keyCode==13)searchCD()">



<button onclick="searchCD()" class="btn btn-info" style="margin-left:5px">🔍</button>



</div>



<div class="card" style="background:#fff8e1;padding:10px;margin-bottom:10px">



<div style="margin-bottom:8px;font-size:16px;font-weight:bold">上传数据</div>



<div>



<span style="font-size:14px">数据名称:</span>



<input id="cdUploadKey" type="text" style="width:200px;padding:4px;border-radius:4px;border:1px solid #ccc" placeholder="输入数据名称">



<input id="cdUploadFile" type="file" accept=".txt,.json,.csv,.md,.xml,.yml,.yaml,.log,.ini,.cfg" style="display:inline-block;margin:0 10px">



<button onclick="uploadTextFile()" class="btn btn-primary" style="background:#2196F3;color:#fff">上传</button>



<span id="cdUploadStatus" style="margin-left:10px;font-size:13px;color:#999"></span>



</div>



</div>



<div style="overflow:auto">



<table class="user-table" style="font-size:13px">



<thead><tr><th>Id</th><th>数据名称</th><th>数据</th><th>数据MD5</th><th>更新时间</th><th>状态</th><th>数据操作</th></tr><th style="width:100px">密码</th></thead>



<tbody id="cdDataBody"></tbody>



</table>



</div>



<nav style="margin-top:10px;text-align:center">



<ul id="cdPagination" class="pagination" style="list-style:none;display:inline-flex;gap:5px;padding:0"></ul>



</nav>



</div>



</div></div>



</div>



</div></div>



</div>



</div></div>



</div>



</div></div>



<div class="tab-page" id="page-apidocs">

<div class="card" style="background:#e8f4fd;padding:15px">

<h3 style="margin-top:0">📖 API 对接文档</h3>

<p style="color:#666;font-size:14px">以下接口供第三方开发者对接使用，需要先获取 Access Token。</p>



<h4 style="margin:15px 0 5px">1. 获取数据列表</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=0<br>

<span style="color:#999">参数：project_id=项目ID, token=项目Token, queryType=0未读/1已读/-1全部</span>

</div>



<h4 style="margin:15px 0 5px">2. 获取单条数据</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>GET</strong> /api/cddata/{data_id}?token={token}<br>

<span style="color:#999">返回该条数据的原始内容（纯文本）</span>

</div>



<h4 style="margin:15px 0 5px">3. 上传数据</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>POST</strong> /api/cddata/{project_id}?token={token}<br>

<span style="color:#999">Body (JSON): {"数据名称": "xxx", "数据": "xxx"}</span>

</div>



<h4 style="margin:15px 0 5px">4. 获取第一条未读数据（自动标已读）</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>GET</strong> /api/cddata/{project_id}/fetchone?token={token}<br>

<span style="color:#999">取该项目下第一条未读数据（按id升序），返回内容后自动标为已读。</span>

</div>



<h4 style="margin:15px 0 5px">5. 标记数据状态</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>POST</strong> /api/cddata/state/{data_id}?token={token}<br>

<span style="color:#999">切换该条数据的已读/未读状态</span>

</div>



<h4 style="margin:15px 0 5px">6. 删除第一条数据（即用即删）</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>GET</strong> /api/cddata/{project_id}/popfirst?token={token}<br>

<span style="color:#999">返回该项目下第一条未读数据（按id升序），返回后直接删除，适合队列式消息处理。</span>

</div>



<h4 style="margin:15px 0 5px">7. 删除数据</h4>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">

<strong>DELETE</strong> /api/cddata/{data_id}?token={token}

</div>



<br>

<h4 style="color:#e74c3c">获取 Token</h4>

<p style="font-size:13px;color:#666">在云数据页面创建项目后，项目详情中会显示对应的 Token。<br>

Token 用于鉴权，请妥善保管。</p>



<h4 style="margin:15px 0 5px">🔗 API 地址</h4>

<p style="font-size:13px;color:#666">当前线上地址：<a href="https://qiezidata-production.up.railway.app" target="_blank">https://qiezidata-production.up.railway.app</a></p>

<p style="font-size:13px;color:#999">所有 API 请在此基础域名上拼接。</p>



<h4 style="margin:15px 0 5px">🤖 懒人精灵调用示例</h4>
<p style="font-size:13px;color:#666;margin:5px 0 10px">基于懒人精灵官方 <code>httpGet</code> / <code>httpPost</code> API (安卓端)</p>

<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace;white-space:pre-wrap">

-- ==============================<br>
-- 获取未读数据列表 (GET)<br>
-- queryType=0=未读, queryType=-1=全部<br>
-- ==============================<br><br>

local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx&amp;queryType=0"<br><br>

local ret, code = httpGet(url, 30)<br>
traceprint(ret)<br><br>

-- ==============================<br>
-- 上传数据 (POST)<br>
-- Body 字段: 数据名称 / 数据<br>
-- ==============================<br><br>

local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx"<br>
local body = '{"数据名称":"test","数据":"hello"}'<br>
local headers = {}<br>
headers["Content-Type"] = "application/json"<br><br>

local ret, code = httpPost(url, body, 30, headers)<br>
traceprint(ret)<br><br>

-- ==============================<br>
-- 获取单条数据 (GET)<br>
-- {data_id} 替换为实际数据ID<br>
-- ==============================<br><br>

local url = "https://qiezidata-production.up.railway.app/api/cddata/123?token=xxx"<br><br>

local ret, code = httpGet(url, 30)<br>
traceprint(ret)<br><br>

-- ==============================<br>
-- 取第一条未读并标已读 (GET)<br>
-- ==============================<br><br>

local url = "https://qiezidata-production.up.railway.app/api/cddata/2/fetchone?token=xxx"<br><br>

local ret, code = httpGet(url, 30)<br>
traceprint(ret)<br><br>

-- ==============================<br>
-- 取第一条未读并删除 (队列模式) (GET)<br>
-- ==============================<br><br>

local url = "https://qiezidata-production.up.railway.app/api/cddata/2/popfirst?token=xxx"<br><br>

local ret, code = httpGet(url, 30)<br>
traceprint(ret)<br><br>

-- ==============================<br>
-- 处理 JSON 返回结果<br>
-- ==============================<br><br>

local ret, code = httpGet(url, 30)<br>
if code == 200 then<br>
&nbsp;&nbsp;&nbsp;&nbsp;local tb = jsonLib.decode(ret)<br>
&nbsp;&nbsp;&nbsp;&nbsp;traceprint("数据名称: " .. tb.data.数据名称)<br>
&nbsp;&nbsp;&nbsp;&nbsp;traceprint("数据内容: " .. tb.data.数据)<br>
end<br><br>

-- ==============================<br>
-- 异步请求 (不阻塞主线程)<br>
-- ==============================<br><br>

function callback(ret, code)<br>
&nbsp;&nbsp;&nbsp;&nbsp;traceprint("收到数据: " .. ret)<br>
end<br><br>

asynHttpGet(callback, url, 30)<br>

</div><div id="toast" class="toast"></div>







<script>



/* v3 */



function switchPage(id,el){document.querySelectorAll('.nav-item').forEach(function(n){n.classList.remove('active')});el.classList.add('active');document.querySelectorAll('.tab-page').forEach(function(p){p.classList.remove('active')});document.getElementById('page-'+id).classList.add('active');if(id==='dashboard')loadDashboard();if(id==='files')loadAllFiles();if(id==='upload')loadMyFiles();if(id==='users')loadUsers();if(id==='clouddata')initCloudData()}



document.getElementById('dropZone').addEventListener('click',function(){document.getElementById('fileInput').click()});document.getElementById('fileInput').addEventListener('change',function(){if(this.files.length)uploadFile(this.files[0])});



document.getElementById('fileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('确认删除文件「'+fname+'」吗？'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadAllFiles();alert('文件已删除')}).catch(function(){alert('删除失败')})})



document.getElementById('myFileList').addEventListener('click',function(e){var btn=e.target.closest('.af-del');if(!btn)return;var fid=btn.dataset.fid;var fname=btn.dataset.fname;if(!confirm('确认删除文件「'+fname+'」吗？'))return;fetch('/admin/file/'+fid,{method:'DELETE',credentials:'include'}).then(function(r){if(!r.ok)throw Error();loadMyFiles();alert('文件已删除')}).catch(function(){alert('删除失败')})})







;



async function uploadFile(file){var fd=new FormData();fd.append('file',file);document.getElementById('uploadProgress').style.display='block';try{var xhr=new XMLHttpRequest();await new Promise(function(resolve,reject){xhr.onload=function(){if(xhr.status===200)resolve();else if(xhr.status===401)window.location.href='/';else reject()};xhr.open('POST','/upload');xhr.withCredentials=true;xhr.send(fd)});showToast('上传成功','success');}catch(e){showToast('上传失败','error')}loadMyFiles();document.getElementById('uploadProgress').style.display='none'}



async function loadDashboard(){try{var r=await fetch('/admin/stats',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();document.getElementById('statUsers').textContent=d.users;document.getElementById('statFiles').textContent=d.files;document.getElementById('statSize').textContent=d.size_display;document.getElementById('statAdmin').textContent=d.admins}catch(e){}}



async function loadAllFiles(){try{var r=await fetch('/admin/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('fileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B | '+f.owner+'</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>下载</a><button class=\"af-del\" data-fid=\"' + f.id + '\" data-fname=\"'+f.original_name+'\">\u5220\u9664</button></div></li>'}h+='</ul>';document.getElementById('fileList').innerHTML=h}catch(e){}}



async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span><button style="margin-left:5px;color:#e74c3c;border:none;background:none;cursor:pointer" onclick="unsetAdmin('+u.id+')">取消管理员</button>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button> <button data-uid="'+u.id+'" class="cpw-btn" style="margin-left:5px" onclick="adminChangePwd('+u.id+')">修改密码</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}



document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.del-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定要删除用户 '+uname+' 吗?此操作不可恢复!'))deleteUser(uid)})



document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定将用户 '+uname+' 设为管理员吗?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('已设为管理员');loadUsers()}else{r.json().then(function(d){alert(d.detail||'设置失败')})}}).catch(function(){alert('请求失败')})}})



document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.cpw-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));adminChangePwd(uid)})




function unsetAdmin(uid){ if(confirm('确定要取消该用户的管理员资格吗?')){ fetch('/admin/user/'+uid+'/unset_admin',{method:'POST',credentials:'include'}).then(function(r){ if(r.ok){ alert('已取消管理员'); loadUsers(); } else { r.json().then(function(d){ alert(d.detail||'操作失败'); }); } }).catch(function(){ alert('请求失败'); }); } }





async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span><button style="margin-left:5px;color:#e74c3c;border:none;background:none;cursor:pointer" onclick="unsetAdmin('+u.id+')">取消管理员</button>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button> <button data-uid="'+u.id+'" class="cpw-btn" style="margin-left:5px" onclick="adminChangePwd('+u.id+')">修改密码</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}async function loadMyFiles(){try{var r=await fetch('/files',{credentials:'include'});if(r.status===401){window.location.href='/';return}var files=await r.json();if(!files.length){document.getElementById('myFileList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">暂无文件</p>';return}var h='<ul class=\"file-list\">';for(var i=0;i<files.length;i++){var f=files[i];h+='<li class=\"file-item\"><div class=\"file-info\"><div class=\"file-name\">'+f.original_name+'</div><div class=\"file-meta\">'+f.size+'B</div></div><div class=\"file-actions\"><a href=\"/download/'+f.id+'\" download>\u4e0b\u8f7d</a><button class=\"af-del\" data-fid=\"' + f.id + '\" data-fname=\"'+f.original_name+'\">\u5220\u9664</button></div></li>'}h+='</ul>';document.getElementById('myFileList').innerHTML=h}catch(e){}}



async function delFile(id){if(!confirm('确定删除？'))return;try{var r=await fetch('/delete/'+id,{method:'DELETE',credentials:'include'});if(r.ok){showToast('删除成功','success');loadMyFiles()}else if(r.status===401)window.location.href='/'}catch(e){}}







async function exportCD(mode){var pid=document.getElementById('cdpSelect').value;var m={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+m[mode]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+mode)}







async function exportCD(mode){var pid=document.getElementById('cdpSelect').value;var m={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+m[mode]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+mode)}











function loadCloudDataProjects(){fetch('/admin/cdprojects',{credentials:'include'}).then(function(r){return r.json()}).then(function(ps){window.cdProjects=ps;var sel=document.getElementById('cdpSelect');if(!sel)return;sel.innerHTML='';for(var i=0;i<ps.length;i++){var o=document.createElement('option');o.value=ps[i].id;o.text='ID:'+ps[i].id+' '+ps[i].name;sel.appendChild(o)}var p=ps[0];if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>';loadCloudDataStats(p.id);loadCloudDataList(p.id,1)}})}



function loadCloudDataStats(pid){fetch('/admin/cdprojects/stats/'+pid,{credentials:'include'}).then(function(r){return r.json()}).then(function(s){document.getElementById('cdTotal').textContent=s.total;document.getElementById('cdNoRead').textContent=s.noRead;document.getElementById('cdRead').textContent=s.read})}



function loadCloudDataList(pid,page){var q=document.getElementById('cdQueryType').value;var s=document.getElementById('cdSearchText').value;var u='/admin/cddata/'+pid+'?page='+page+'&limit=20&queryType='+q+(s?'&search='+encodeURIComponent(s):'');fetch(u,{credentials:'include'}).then(function(r){return r.json()}).then(function(d){var tb=document.getElementById('cdDataBody');if(!tb)return;tb.innerHTML='';for(var i=0;i<d.items.length;i++){var x=d.items[i];var st=x.read?'已读取':'未读取';var sc=st==='已读取'?'green':'orange';var btnT=x.read?'修改为未读取':'修改为已读取';tb.innerHTML+='<tr><td>'+x.id+'</td><td>'+x.name+'</td><td><a href=\"#\" onclick=\"downloadCD('+x.id+');return false\">(点击下载)</a></td><td>'+x.md5+'</td><td>'+(x.t||'')+'</td><td><span style=\"color:'+sc+'\">'+st+'</span></td><td><button onclick=\"toggleCDState('+x.id+')\" class=\"mybtn btn btn-danger\">'+btnT+'</button> <button onclick=\"if(confirm("确定删除?"))deleteCD('+x.id+')\" class=\"mybtn btn btn-danger\">删除数据</button></td></tr>'}window.cdPage=page;window.cdTotal=d.total;var pn=Math.ceil(d.total/20)||1;var ph='<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+',1);return false\">首页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.max(1,page-1)+');return false\">上一页</a></li>';for(var i=1;i<=pn;i++){ph+='<li class=\"'+(i===page?'active':'')+'\"><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+i+');return false\">'+i+'</a></li>'}ph+='<li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+Math.min(pn,page+1)+');return false\">下一页</a></li><li><a href=\"#\" onclick=\"loadCloudDataList('+pid+','+pn+');return false\">尾页</a></li>';document.getElementById('cdPagination').innerHTML=ph})}



function toggleCDState(cid){fetch('/admin/cddata/state/'+cid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)}})}



function deleteCD(cid){var pid=document.getElementById('cdpSelect').value;fetch('/admin/cddata/'+cid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,window.cdPage||1);loadCloudDataStats(pid)})}



function uploadTextFile(){var key=document.getElementById('cdUploadKey').value.trim();var fileInput=document.getElementById('cdUploadFile');if(!fileInput.files||!fileInput.files[0]){alert('请选择文件');return}if(!key)key=fileInput.files[0].name.replace(/\.[^.]+$/,'');var pid=document.getElementById('cdpSelect').value;if(!pid){alert('请先选择项目');return}var reader=new FileReader();reader.onload=function(e){var val=e.target.result;fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:key,value:val,project_id:parseInt(pid)})}).then(function(r){if(r.ok){document.getElementById('cdUploadStatus').textContent='上传成功: '+key;document.getElementById('cdUploadKey').value='';fileInput.value='';loadCloudDataList(pid,1)}else{alert('上传失败')}}).catch(function(){alert('上传失败')})};reader.readAsText(fileInput.files[0])}



function resetToken(pid){if(!confirm('重置后旧Token失效，确定重置吗?'))return;fetch('/admin/cdprojects/resettoken/'+pid,{method:'POST',credentials:'include'}).then(function(r){return r.json()}).then(function(d){if(d.ok){document.getElementById('cdpToken_'+pid).textContent=d.token;showToast('重置成功','success')}})}



function resetAllRead(pid){if(!confirm('确定将所有数据设为未读取?'))return;fetch('/admin/cdprojects/resetallread/'+pid,{method:'POST',credentials:'include'}).then(function(){loadCloudDataStats(pid);loadCloudDataList(pid,1)})}



function createProject(){var n=prompt('请输入key标识符称:');if(!n)return;fetch('/admin/cdprojects',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({name:n})}).then(function(){loadCloudDataProjects();showToast('创建成功','success')})}



function deleteProject(){var pid=document.getElementById('cdpSelect').value;if(!confirm('删除项目会清空所有数据，确定删除吗?'))return;fetch('/admin/cdprojects/'+pid,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataProjects();showToast('删除成功','success')})}



function exportCD(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部',read:'已读取',unread:'未读取'};if(!confirm('确定导出'+t[m]+'?'))return;window.open('/admin/cddata/export/'+pid+'/'+m)}



function batchDelete(m){var pid=document.getElementById('cdpSelect').value;var t={all:'全部数据',read:'已读取数据',unread:'未读取数据'};if(!confirm('确定删除'+t[m]+'?'))return;fetch('/admin/cddata/batch/'+pid+'?mode='+m,{method:'DELETE',credentials:'include'}).then(function(){loadCloudDataList(pid,1);loadCloudDataStats(pid);showToast('删除成功','success')})}



function searchCD(){var pid=document.getElementById('cdpSelect').value;loadCloudDataList(pid,1)}



function downloadCD(cid){window.open('/admin/cddata/download/'+cid)}



function initCloudData(){var sel=document.getElementById('cdpSelect');if(!sel)return;sel.onchange=function(){var pid=this.value;if(!pid)return;var p=window.cdProjects.find(function(x){return x.id==pid});if(p){document.getElementById('cdpTableBody').innerHTML='<tr><td>'+p.id+'</td><td>'+p.name+'</td><td id=\"cdpToken_'+p.id+'\">'+p.token+'</td><td>'+(p.t||'')+'</td><td><button onclick=\"resetToken('+p.id+')\" class=\"mybtn btn btn-danger\">重置TOKEN</button></td></tr>'}loadCloudDataStats(pid);loadCloudDataList(pid,1)};document.getElementById('cdQueryType').onchange=function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)};loadCloudDataProjects()}



document.addEventListener('DOMContentLoaded',function(){initCloudData();loadDashboard();});
function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }

function openProfileModal(){ fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(d){document.getElementById('profModalUser').value=d.username||'';document.getElementById('profModalDN').value=d.display_name||'';document.getElementById('profModalRole').value=d.role||'user';document.getElementById('profModalSaveMsg').style.display='none';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';document.getElementById('profModalPwdMsg').style.display='none';document.getElementById('profileModal').style.display='flex';}).catch(function(){alert('获取个人资料失败');}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;} if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='两次输入不一致';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
var _cpUid=0;
function adminChangePwd(uid){ _cpUid=uid; document.getElementById('changePasswordModal').style.display='flex'; document.getElementById('cpUserInfo').textContent='用户ID: '+uid; document.getElementById('cpNewPwd').value=''; document.getElementById('cpMsg').style.display='none'; }
function submitAdminChangePwd(){ var newP=document.getElementById('cpNewPwd').value; var cP=document.getElementById('cpConfirmPwd').value; var msg=document.getElementById('cpMsg'); msg.style.display='none'; if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!=cP){msg.textContent='两次密码不一致';msg.style.display='block';return;} fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
</script>






<div id="role-indicator" data-role="<!--R-->" style="display:none"></div>
<script>
(function(){var e=document.getElementById("role-indicator");var r=e?e.dataset.role:"";if(r!="admin"){document.querySelectorAll('[onclick*="dashboard"],[onclick*="users"]').forEach(function(n){n.style.display="none"});}})();

function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;} if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='两次输入不一致';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
var _cpUid=0;
function adminChangePwd(uid){ _cpUid=uid; document.getElementById('changePasswordModal').style.display='flex'; document.getElementById('cpUserInfo').textContent='用户ID: '+uid; document.getElementById('cpNewPwd').value=''; document.getElementById('cpMsg').style.display='none'; }
function submitAdminChangePwd(){ var newP=document.getElementById('cpNewPwd').value; var msg=document.getElementById('cpMsg'); msg.style.display='none'; if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
</script>

<!-- 个人资料弹窗 -->
<div id="profileModal" class="modal" style="display:none"><div class="modal-content" style="max-width:420px"><span class="modal-close" onclick="closeProfile()">&times;</span><h3>个人资料</h3><div class="form-group"><label>用户名</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><div class="form-group"><label>显示名称</label><input id="profModalDN" type="text" placeholder="输入显示名称"></div><div class="form-group"><label>角色</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><button class="btn" onclick="saveProfileModal()">保存</button><div id="profModalSaveMsg" class="msg" style="display:none"></div><hr style="margin:16px 0"><h4>修改密码</h4><div class="form-group"><label>旧密码</label><input id="profModalOldPwd" type="password" placeholder="输入旧密码"></div><div class="form-group"><label>新密码</label><input id="profModalNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认新密码</label><input id="profModalNewPwd2" type="password" placeholder="再次输入"></div><button class="btn" onclick="submitProfilePwdModal()">修改密码</button><div id="profModalPwdMsg" class="msg" style="display:none"></div></div></div>
<!-- 管理员改用户密码 -->
<div id="changePasswordModal" class="modal" style="display:none"><div class="modal-content" style="max-width:380px"><span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span><h3>修改用户密码</h3><p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p><div class="form-group"><label>新密码</label><input id="cpNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认密码</label><input id="cpConfirmPwd" type="password" placeholder="再次输入新密码"></div><button class="btn" onclick="submitAdminChangePwd()">确认修改</button><div id="cpMsg" class="msg" style="display:none"></div></div></div>

</body></html>"""























# ---- CloudData Project API ----



@app.get('/admin/cdprojects')



async def cdprojects_list(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        r = await db_fetch("SELECT id,name,token,to_char(created_at,'YYYY-MM-DD HH24:MI') AS t FROM clouddata_projects ORDER BY id DESC")



    else:



        r = await db_fetch('SELECT id AS "id",name,token,created_at AS t FROM clouddata_projects ORDER BY id DESC')



    return r







@app.post('/admin/cdprojects')



async def cdprojects_create(request: Request):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    body = await request.json(); name = body.get('name','')



    import uuid



    token = uuid.uuid4().hex[:32]



    if use_pg:



        await db_execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", name, token)



    else:



        await db_execute("INSERT INTO clouddata_projects (name,token,created_at) VALUES (?,?,?)", name, token, datetime.utcnow().isoformat())



    return {'ok':True}







@app.delete('/admin/cdprojects/{pid}')



async def cdprojects_delete(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    await db_execute("DELETE FROM clouddata WHERE project_id=?", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1", pid)



    if use_pg:



        await db_execute("DELETE FROM clouddata_projects WHERE id=$1", pid)



    else:



        await db_execute("DELETE FROM clouddata_projects WHERE id=?", pid)



    return {'ok':True}







@app.post('/admin/cdprojects/resettoken/{pid}')



async def cdprojects_reset_token(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    import uuid



    token = uuid.uuid4().hex[:32]



    if use_pg:



        await db_execute("UPDATE clouddata_projects SET token=$1 WHERE id=$2", token, pid)



    else:



        await db_execute("UPDATE clouddata_projects SET token=? WHERE id=?", token, pid)



    return {'ok':True, 'token':token}







@app.post('/admin/cdprojects/resetallread/{pid}')



async def cdprojects_reset_all_read(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        await db_execute("UPDATE clouddata SET read=FALSE WHERE project_id=$1", pid)



    else:



        await db_execute("UPDATE clouddata SET read=0 WHERE project_id=?", pid)



    return {'ok':True}







@app.get('/admin/cdprojects/stats/{pid}')



async def cdprojects_stats(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        async with db_pool.acquire() as conn:



            total = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1", pid)



            no_read = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)



            read_cnt = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)



    else:



        conn = sqlite3.connect('/data/files.db')



        total = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=?", (pid,)).fetchone()[0]



        no_read = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=0", (pid,)).fetchone()[0]



        read_cnt = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=1", (pid,)).fetchone()[0]



        conn.close()



    return {'total':total, 'noRead':no_read, 'read':read_cnt}







@app.get('/api/cddata/{project_id}/fetchone')

async def api_fetch_one_cddata(project_id: int, request: Request):

    token = request.query_params.get('token','')

    if not token:

        return JSONResponse({'ok':False,'detail':'no token'}, status_code=403)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT token FROM clouddata_projects WHERE id=$1', project_id)

            if not row or row['token'] != token:

                return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

            row = await conn.fetchrow('SELECT id, v FROM clouddata WHERE project_id=$1 AND read=FALSE ORDER BY id ASC LIMIT 1', project_id)

            if not row:

                return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)

            val = row['v']

            await conn.execute('UPDATE clouddata SET read=TRUE WHERE id=$1', row['id'])

            return PlainTextResponse(val)

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT token FROM clouddata_projects WHERE id=?', (project_id,))

        row = cur.fetchone()

        if not row or row[0] != token:

            conn.close()

            return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

        cur.execute('SELECT id, v FROM clouddata WHERE project_id=? AND read=0 ORDER BY id ASC LIMIT 1', (project_id,))

        row = cur.fetchone()

        if not row:

            conn.close()

            return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)

        val = row[1]

        cur.execute('UPDATE clouddata SET read=1 WHERE id=?', (row[0],))

        conn.commit(); conn.close()

        return PlainTextResponse(val)



@app.get('/api/cddata/{project_id}/popfirst')

async def api_pop_first_cddata(project_id: int, request: Request):

    token = request.query_params.get('token','')

    if not token:

        return JSONResponse({'ok':False,'detail':'no token'}, status_code=403)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT token FROM clouddata_projects WHERE id=$1', project_id)

            if not row or row['token'] != token:

                return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

            row = await conn.fetchrow('SELECT id, v FROM clouddata WHERE project_id=$1 AND read=FALSE ORDER BY id ASC LIMIT 1', project_id)

            if not row:

                return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)

            val = row['v']

            await conn.execute('DELETE FROM clouddata WHERE id=$1', row['id'])

            return PlainTextResponse(val)

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT token FROM clouddata_projects WHERE id=?', (project_id,))

        row = cur.fetchone()

        if not row or row[0] != token:

            conn.close()

            return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

        cur.execute('SELECT id, v FROM clouddata WHERE project_id=? AND read=0 ORDER BY id ASC LIMIT 1', (project_id,))

        row = cur.fetchone()

        if not row:

            conn.close()

            return JSONResponse({'ok':False,'detail':'no unread data'}, status_code=404)

        val = row[1]

        cur.execute('DELETE FROM clouddata WHERE id=?', (row[0],))

        conn.commit(); conn.close()

        return PlainTextResponse(val)



@app.get('/api/cddata/{data_id}')

async def api_get_cddata(request: Request, data_id: int):

    token = request.query_params.get('token','')

    if not token:

        return JSONResponse({'ok':False,'detail':'no token'}, status_code=403)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT cd.*, cp.token as pt FROM clouddata cd LEFT JOIN clouddata_projects cp ON cd.project_id=cp.id WHERE cd.id=$1', data_id)

            if not row or row['pt'] != token:

                return JSONResponse({'ok':False,'detail':'not found or token mismatch'}, status_code=404)

            await conn.execute('UPDATE clouddata SET read=TRUE WHERE id=$1', data_id)

            return PlainTextResponse(row['v'])

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT cd.id, cd.v, cp.token FROM clouddata cd LEFT JOIN clouddata_projects cp ON cd.project_id=cp.id WHERE cd.id=?', (data_id,))

        row = cur.fetchone()

        if not row or row[2] != token:

            conn.close()

            return JSONResponse({'ok':False,'detail':'not found or token mismatch'}, status_code=404)

        cur.execute('UPDATE clouddata SET read=1 WHERE id=?', (data_id,))

        conn.commit(); conn.close()

        return PlainTextResponse(row[1])



@app.post('/api/cddata/{project_id}')

async def api_post_cddata(project_id: int, request: Request):

    b = await request.json(); k = b.get('数据名称','').strip(); v = b.get('数据','').strip()

    token = request.query_params.get('token','')

    if not k or not v or not token:

        return JSONResponse({'ok':False,'detail':'missing params'}, status_code=400)

    if use_pg:

        async with db_pool.acquire() as conn:

            row = await conn.fetchrow('SELECT token FROM clouddata_projects WHERE id=$1', project_id)

            if not row or row['token'] != token:

                return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

            name = k; md5 = hashlib.md5(v.encode()).hexdigest()

            await conn.execute('DELETE FROM clouddata WHERE project_id=$1 AND k=$2', project_id, k)

            await conn.execute('INSERT INTO clouddata(project_id,k,v,name,md5) VALUES($1,$2,$3,$4,$5)', project_id, k, v, name, md5)

    else:

        conn = sqlite3.connect(DB_PATH)

        cur = conn.cursor()

        cur.execute('SELECT token FROM clouddata_projects WHERE id=?', (project_id,))

        row = cur.fetchone()

        if not row or row[0] != token:

            conn.close()

            return JSONResponse({'ok':False,'detail':'token mismatch'}, status_code=403)

        name = k; md5 = hashlib.md5(v.encode()).hexdigest()

        cur.execute('DELETE FROM clouddata WHERE project_id=? AND k=?', (project_id, k))

        cur.execute('INSERT INTO clouddata(project_id,k,v,name,md5) VALUES(?,?,?,?,?)', (project_id, k, v, name, md5))

        conn.commit(); conn.close()

    return JSONResponse({'ok':True, 'key':k})



@app.get('/admin/cddata/{pid}')



async def cddata_list(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    page = int(request.query_params.get('page',1)); limit = int(request.query_params.get('limit',20))



    queryType = int(request.query_params.get('queryType', -1))  # -1=all, 0=unread, 1=read



    search = request.query_params.get('search','')



    offset = (page-1)*limit







    where = f"WHERE project_id='{pid}'"



    if queryType == 0: where += " AND read=FALSE" if use_pg else " AND read=0"



    elif queryType == 1: where += " AND read=TRUE" if use_pg else " AND read=1"



    if search: where += f" AND name LIKE '%{search}%'"







    if use_pg:



        async with db_pool.acquire() as conn:



            total = await conn.fetchval(f"SELECT COUNT(*)::int FROM clouddata {where}")



            r = await conn.fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")



            r = [dict(row) for row in r]



    else:



        conn = sqlite3.connect('/data/files.db')



        total = conn.execute(f"SELECT COUNT(*) FROM clouddata {where}").fetchone()[0]



        r = conn.execute(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}").fetchall()



        r = [dict(zip([desc[0] for desc in conn.execute(f'SELECT id,k,v,name,md5,t,read FROM clouddata {where} LIMIT 1').description], row)) for row in r]



        conn.close()



    return {'items': r, 'total': total}







@app.post('/admin/cddata/state/{cid}')



async def cddata_toggle_state(request: Request, cid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        async with db_pool.acquire() as conn:



            await conn.execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)



            val = await conn.fetchval("SELECT read FROM clouddata WHERE id=$1", cid)



    else:



        conn = sqlite3.connect('/data/files.db')



        conn.execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", (cid,))



        val = conn.execute("SELECT read FROM clouddata WHERE id=?", (cid,)).fetchone()[0]



        conn.commit(); conn.close()



    return {'ok':True, 'read': bool(val)}







@app.delete('/admin/cddata/{cid}')



async def cddata_delete(request: Request, cid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    await db_execute("DELETE FROM clouddata WHERE id=?", cid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE id=$1", cid)



    return {'ok':True}







@app.delete('/admin/cddata/batch/{pid}')



async def cddata_batch_delete(request: Request, pid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    mode = request.query_params.get('mode','all')  # all, read, unread



    if mode == 'all':



        await db_execute("DELETE FROM clouddata WHERE project_id=?", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1", pid)



    elif mode == 'read':



        await db_execute("DELETE FROM clouddata WHERE project_id=? AND read=1", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)



    elif mode == 'unread':



        await db_execute("DELETE FROM clouddata WHERE project_id=? AND read=0", pid) if not use_pg else await db_execute("DELETE FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)



    return {'ok':True}







@app.get('/admin/cddata/export/{pid}/{mode}')



async def cddata_export(request: Request, pid: int, mode: str):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    where = f"WHERE project_id='{pid}'"



    if mode == 'read': where += " AND read=TRUE" if use_pg else " AND read=1"



    elif mode == 'unread': where += " AND read=FALSE" if use_pg else " AND read=0"



    



    if use_pg:



        async with db_pool.acquire() as conn:



            raw = await conn.fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC")



            r = [dict(row) for row in raw]



    else:



        conn = sqlite3.connect('/data/files.db')



        raw = conn.execute(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC").fetchall()



        r = [dict(zip([desc[0] for desc in conn.execute(f'SELECT id,k,v,name,md5,t,read FROM clouddata {where} LIMIT 1').description], row)) for row in raw]



        conn.close()



    



    import csv, io



    out = io.StringIO()



    writer = csv.writer(out)



    writer.writerow(['ID','数据名称','数据','Name','MD5','更新时间','状态'])



    for row in r:



        writer.writerow([row['id'],row['k'],row['v'],row.get('name',''),row.get('md5',''),row['t'],'已读' if row['read'] else '未读'])



    csv_bytes = out.getvalue().encode('utf-8-sig')



    return Response(content=csv_bytes, media_type='text/csv', headers={'Content-Disposition': f'attachment; filename=clouddata_{pid}_{mode}.csv'})







@app.get('/admin/cddata/download/{cid}')



async def cddata_download(request: Request, cid: int):



    admin_id = _require(request); admin_user = await _user(admin_id)



    if not admin_user or admin_user.get('role') != 'admin': raise HTTPException(status_code=403)



    if use_pg:



        async with db_pool.acquire() as conn:



            raw = await conn.fetchrow("SELECT k,v FROM clouddata WHERE id=$1", cid)



            r = [dict(raw)] if raw else []



    else:



        conn = sqlite3.connect('/data/files.db')



        raw = conn.execute("SELECT k,v FROM clouddata WHERE id=?", (cid,)).fetchone()



        r = [{'k':raw[0],'v':raw[1]}] if raw else []



        conn.close()



    if not r: raise HTTPException(status_code=404)



    data = r[0]['v'].encode('utf-8')



    return Response(content=data, media_type='text/plain', headers={'Content-Disposition': f'attachment; filename={r[0]["k"]}.txt'})







if __name__ == '__main__':



    import uvicorn



    uvicorn.run(app, host=HOST, port=PORT)















# deploy 07/21/2026 03:27:38









# build_1784643100
# deploy trigger 


_ENV_TEMPLATE = """# Railway Environment Variables
# _LOGIN = login page HTML
# _ADMIN = admin page HTML
"""