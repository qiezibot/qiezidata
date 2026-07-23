# -*- coding: utf-8 -*-
# Add clouddata: DB tables + admin APIs + script APIs
# Does NOT touch HTML templates (they stay English)

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 1. PG clouddata table (after files table, inside async with) =====
old_pg = "            await conn.execute('CREATE TABLE IF NOT EXISTS users"
new_pg = (
    "            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata("
    "id SERIAL PRIMARY KEY,k VARCHAR(255) UNIQUE NOT NULL,v TEXT NOT NULL,"
    "t TIMESTAMP DEFAULT CURRENT_TIMESTAMP,read BOOLEAN NOT NULL DEFAULT FALSE)')\n"
    "            # clouddata column migration\n"
    "            try:\n"
    "                cdcols = await conn.fetch("
    '"SELECT column_name FROM information_schema.columns WHERE table_name=$1", '
    "'clouddata')\n"
    "                if 'read' not in [c['column_name'] for c in cdcols]:\n"
    '                    await conn.execute("ALTER TABLE clouddata ADD COLUMN '
    "read BOOLEAN NOT NULL DEFAULT FALSE\")\n"
    "            except: pass\n"
    "\n"
    "            await conn.execute('CREATE TABLE IF NOT EXISTS users"
)
content = content.replace(old_pg, new_pg, 1)

# ===== 2. SQLite clouddata table =====
old_sql = "        conn.execute('CREATE TABLE IF NOT EXISTS users"
new_sql = (
    "        conn.execute('CREATE TABLE IF NOT EXISTS clouddata("
    "id INTEGER PRIMARY KEY AUTOINCREMENT,k TEXT UNIQUE NOT NULL,"
    "v TEXT NOT NULL,t TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0)')\n"
    "        try: conn.execute('ALTER TABLE clouddata ADD COLUMN read INTEGER NOT NULL DEFAULT 0')\n"
    "        except: pass\n"
    "\n"
    "        conn.execute('CREATE TABLE IF NOT EXISTS users"
)
content = content.replace(old_sql, new_sql, 1)

# ===== 3. Add admin clouddata API routes =====
admin_api = """

@app.get('/admin/clouddata')
async def clouddata_list(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        return await db_execute("SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata ORDER BY id DESC")
    else:
        return await db_execute('SELECT id,k,v,t,read FROM clouddata ORDER BY id DESC')

@app.post('/admin/clouddata/add')
async def clouddata_add(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    b = await request.json(); k = b.get('key','').strip(); v = b.get('value','').strip()
    if not k or not v: raise HTTPException(400)
    if use_pg:
        await db_execute('INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2', k, v)
    else:
        await db_execute('INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)', k, v)
    return {'ok': True}

@app.delete('/admin/clouddata/{cid}')
async def clouddata_del(cid: int, request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        await db_execute('DELETE FROM clouddata WHERE id=$1', cid)
    else:
        await db_execute('DELETE FROM clouddata WHERE id=?', cid)
    return {'ok': True}

"""

content = content.replace("@app.get('/admin/stats')", admin_api + "@app.get('/admin/stats')", 1)

# ===== 4. Add script-facing clouddata APIs =====
script_api = """

@app.post('/clouddata')
async def script_cd_upsert(request: Request):
    uid = _require(request)
    b = await request.json(); k = b.get('key','').strip(); v = b.get('value','').strip()
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
        if use_pg:
            r = await db_execute('SELECT k,v,t,read FROM clouddata WHERE k=$1', key)
            return {'key':r['k'],'value':r['v'],'time':str(r['t']),'read':r['read']} if r else {'error':'not found'}
        else:
            rows = await db_execute('SELECT k,v,t,read FROM clouddata WHERE k=?', key)
            return {'key':rows[0]['k'],'value':rows[0]['v'],'time':rows[0]['t'],'read':rows[0]['read']} if rows else {'error':'not found'}
    if use_pg:
        r = await db_execute('SELECT k,v,t,read FROM clouddata ORDER BY id DESC')
    else:
        r = await db_execute('SELECT k,v,t,read FROM clouddata ORDER BY id DESC')
    return [{'key':x['k'],'value':x['v'],'time':str(x['t']) if x['t'] else '','read':x['read']} for x in r]

@app.get('/clouddata/{key}')
async def script_cd_get(key: str, request: Request):
    _require(request)
    if use_pg:
        r = await db_execute('SELECT k,v,t,read FROM clouddata WHERE k=$1', key)
    else:
        r = await db_execute('SELECT k,v,t,read FROM clouddata WHERE k=?', key)
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

@app.get('/clouddata/export/{mode}')
async def script_cd_export(mode: str, request: Request):
    _require(request)
    if mode == 'all':
        r = await db_execute('SELECT k,v,t,read FROM clouddata ORDER BY id')
    elif mode == 'read':
        sql = 'SELECT k,v,t,read FROM clouddata WHERE read=true ORDER BY id' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE read=1 ORDER BY id'
        r = await db_execute(sql)
    elif mode == 'unread':
        sql = 'SELECT k,v,t,read FROM clouddata WHERE read=false ORDER BY id' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE read=0 ORDER BY id'
        r = await db_execute(sql)
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

"""

# Insert script APIs before admin APIs
content = content.replace(admin_api, script_api + admin_api, 1)

# ===== 5. Add Response import =====
if 'Response' not in content.split('from fastapi.responses import')[1].split('\n')[0]:
    content = content.replace(
        'from fastapi.responses import RedirectResponse',
        'from fastapi.responses import RedirectResponse, Response',
        1
    )

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Size: {len(content)} bytes")

import py_compile
try:
    py_compile.compile('railway_file_server.py', doraise=True)
    print("py_compile OK!")
except py_compile.PyCompileError as e:
    lines = content.split('\n')
    m = __import__('re').search(r'line (\d+)', str(e))
    if m:
        ln = int(m.group(1))
        for i in range(max(0,ln-3), min(len(lines),ln+2)):
            print(f"{i+1} [{len(lines[i])-len(lines[i].lstrip())}sp]: {lines[i][:120]}")
    print("ERROR:", e)

# Verbose check
import re
for fn in ['script_cd_upsert', 'script_cd_list', 'script_cd_get', 'script_cd_delete',
           'script_cd_export', 'script_cd_mark', 'script_cd_mark_id',
           'clouddata_list', 'clouddata_add', 'clouddata_del']:
    cnt = len(list(re.finditer(r'^async def ' + fn + r'\b', content, re.MULTILINE)))
    print(f"  {fn}: {cnt}")
