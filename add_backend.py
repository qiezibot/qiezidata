# -*- coding: utf-8 -*-
# Add clouddata backend APIs + DB table to railway_file_server.py

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== 1. Add clouddata table to init_db =====
# Inside async with block (PG)
old_pg = "            await conn.execute('CREATE TABLE IF NOT EXISTS users"
new_pg = ("            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata("
          "id SERIAL PRIMARY KEY,k VARCHAR(255) UNIQUE NOT NULL,v TEXT NOT NULL,"
          "t TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')\n"
          "\n"
          "            await conn.execute('CREATE TABLE IF NOT EXISTS users")
content = content.replace(old_pg, new_pg, 1)

# SQLite branch
old_sqlite = '        conn.execute("CREATE TABLE IF NOT EXISTS users'
new_sqlite = ("        conn.execute('CREATE TABLE IF NOT EXISTS clouddata("
              "id INTEGER PRIMARY KEY AUTOINCREMENT,k TEXT UNIQUE NOT NULL,"
              "v TEXT NOT NULL,t TEXT NOT NULL)')\n"
              "\n"
              "        conn.execute(\"CREATE TABLE IF NOT EXISTS users'")

# Since the sqlite line has double quotes, let me find it differently
import re
# Find the SQLite users table creation line
sqlite_users = 'conn.execute("CREATE TABLE IF NOT EXISTS users '
idx = content.find(sqlite_users)
if idx > 0:
    # Find the block start (8-space indent)
    line_start = content.rfind('\n', 0, idx) + 1
    insert_point = line_start  # Insert before this line
    to_insert = ("        conn.execute('CREATE TABLE IF NOT EXISTS clouddata("
                 "id INTEGER PRIMARY KEY AUTOINCREMENT,k TEXT UNIQUE NOT NULL,"
                 "v TEXT NOT NULL,t TEXT NOT NULL)')\n")
    content = content[:insert_point] + to_insert + content[insert_point:]
    print("Inserted SQLite clouddata table at line %d" % len(content[:insert_point].split('\n')))

# ===== 2. Add API routes =====
# Find existing API routes - add after the existing admin routes
# Look for the last route before @app.get('/admin/stats')
stats_route = "@app.get('/admin/stats')"
api_block = """
@app.get('/admin/clouddata')
async def clouddata_list(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        return await db_fetch(\"SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t FROM clouddata ORDER BY id DESC\")
    else:
        return await db_fetch('SELECT id,k,v,t FROM clouddata ORDER BY id DESC')

@app.post('/admin/clouddata/add')
async def clouddata_add(request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    b = await request.json(); k = b.get('key','').strip(); v = b.get('value','').strip()
    if not k or not v: raise HTTPException(400)
    if use_pg:
        await db_exec('INSERT INTO clouddata(k,v) VALUES($1,$2) ON CONFLICT(k) DO UPDATE SET v=$2', k, v)
    else:
        await db_exec('INSERT OR REPLACE INTO clouddata(k,v) VALUES(?,?)', k, v)
    return {'ok': True}

@app.delete('/admin/clouddata/{cid}')
async def clouddata_del(cid: int, request: Request):
    uid = _require(request); user = await _user(uid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
    if use_pg:
        await db_exec('DELETE FROM clouddata WHERE id=$1', cid)
    else:
        await db_exec('DELETE FROM clouddata WHERE id=?', cid)
    return {'ok': True}

"""

content = content.replace(stats_route, api_block + stats_route, 1)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Size: {len(content)} bytes")
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")

# Verify all pieces
for t in ['clouddata', '云数据', 'loadCloudData', 'addCloudData', 'delCloudData',
          'admin/clouddata', '/admin/clouddata/add', '/admin/clouddata/{cid}',
          'clouddata(id SERIAL', 'clouddata(id INTEGER']:
    if t not in content:
        print(f"WARNING: missing {t}")
    else:
        print(f"  OK: {t[:40]}")

print("DONE!")
