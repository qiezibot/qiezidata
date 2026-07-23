c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Fix cdprojects_stats - replace db_fetchval with raw SQL for pg
old_stats = '''    if use_pg:
        total = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1", pid)
        no_read = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)
        read_cnt = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)
    else:
        total = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=?", pid)
        no_read = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=0", pid)
        read_cnt = await db_fetchval("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=1", pid)'''

new_stats = '''    if use_pg:
        async with db_pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1", pid)
            no_read = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1 AND read=FALSE", pid)
            read_cnt = await conn.fetchval("SELECT COUNT(*)::int FROM clouddata WHERE project_id=$1 AND read=TRUE", pid)
    else:
        conn = sqlite3.connect('/data/files.db')
        total = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=?", (pid,)).fetchone()[0]
        no_read = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=0", (pid,)).fetchone()[0]
        read_cnt = conn.execute("SELECT COUNT(*) FROM clouddata WHERE project_id=? AND read=1", (pid,)).fetchone()[0]
        conn.close()'''

assert old_stats in c, 'stats function not found!'
c = c.replace(old_stats, new_stats)
print('Stats function fixed')

# Fix cddata_list - use raw pg connections too
old_cddata = '''    if use_pg:
        total = await db_fetchval(f"SELECT COUNT(*) FROM clouddata {where}")
        r = await db_fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")
    else:
        total = await db_fetchval(f"SELECT COUNT(*) FROM clouddata {where}")
        r = await db_fetch(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")'''

new_cddata = '''    if use_pg:
        async with db_pool.acquire() as conn:
            total = await conn.fetchval(f"SELECT COUNT(*)::int FROM clouddata {where}")
            r = await conn.fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}")
            r = [dict(row) for row in r]
    else:
        conn = sqlite3.connect('/data/files.db')
        total = conn.execute(f"SELECT COUNT(*) FROM clouddata {where}").fetchone()[0]
        r = conn.execute(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC LIMIT {limit} OFFSET {offset}").fetchall()
        r = [dict(zip([desc[0] for desc in conn.execute(f'SELECT id,k,v,name,md5,t,read FROM clouddata {where} LIMIT 1').description], row)) for row in r]
        conn.close()'''

assert old_cddata in c, 'cddata_list not found!'
c = c.replace(old_cddata, new_cddata)
print('cddata_list function fixed')

# Fix export
old_export = '''    if use_pg:
        r = await db_fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC")
    else:
        r = await db_fetch(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC")'''

new_export = '''    if use_pg:
        async with db_pool.acquire() as conn:
            raw = await conn.fetch(f"SELECT id,k,v,name,md5,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata {where} ORDER BY id DESC")
            r = [dict(row) for row in raw]
    else:
        conn = sqlite3.connect('/data/files.db')
        raw = conn.execute(f"SELECT id,k,v,name,md5,t,read FROM clouddata {where} ORDER BY id DESC").fetchall()
        r = [dict(zip([desc[0] for desc in conn.execute(f'SELECT id,k,v,name,md5,t,read FROM clouddata {where} LIMIT 1').description], row)) for row in raw]
        conn.close()'''

assert old_export in c, 'export function not found!'
c = c.replace(old_export, new_export)
print('export function fixed')

# Fix download  
old_download = '''    if use_pg:
        r = await db_fetch("SELECT k,v FROM clouddata WHERE id=$1", cid)
    else:
        r = await db_fetch("SELECT k,v FROM clouddata WHERE id=?", cid)'''

new_download = '''    if use_pg:
        async with db_pool.acquire() as conn:
            raw = await conn.fetchrow("SELECT k,v FROM clouddata WHERE id=$1", cid)
            r = [dict(raw)] if raw else []
    else:
        conn = sqlite3.connect('/data/files.db')
        raw = conn.execute("SELECT k,v FROM clouddata WHERE id=?", (cid,)).fetchone()
        r = [{'k':raw[0],'v':raw[1]}] if raw else []
        conn.close()'''

assert old_download in c, 'download function not found!'
c = c.replace(old_download, new_download)
print('download function fixed')

# Fix toggle state
old_toggle = '''    if use_pg:
        await db_execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=$1", cid)
    else:
        await db_execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=?", cid)'''

new_toggle = '''    if use_pg:
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)
            val = await conn.fetchval("SELECT read FROM clouddata WHERE id=$1", cid)
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", (cid,))
        val = conn.execute("SELECT read FROM clouddata WHERE id=?", (cid,)).fetchone()[0]
        conn.commit(); conn.close()
    return {'ok':True, 'read': bool(val)}'''

# Need to handle the return being separate
# Replace differently
old_toggle2 = '''    if use_pg:
        await db_execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=$1", cid)
    else:
        await db_execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", cid)
        r = await db_fetch("SELECT read FROM clouddata WHERE id=?", cid)
    return {'ok':True, 'read': bool(r[0]['read']) if r else False}'''

new_toggle2 = '''    if use_pg:
        async with db_pool.acquire() as conn:
            await conn.execute("UPDATE clouddata SET read=NOT read WHERE id=$1", cid)
            val = await conn.fetchval("SELECT read FROM clouddata WHERE id=$1", cid)
    else:
        conn = sqlite3.connect('/data/files.db')
        conn.execute("UPDATE clouddata SET read = CASE WHEN read=0 THEN 1 ELSE 0 END WHERE id=?", (cid,))
        val = conn.execute("SELECT read FROM clouddata WHERE id=?", (cid,)).fetchone()[0]
        conn.commit(); conn.close()
    return {'ok':True, 'read': bool(val)}'''

assert old_toggle2 in c, 'toggle function not found!'
c = c.replace(old_toggle2, new_toggle2)
print('toggle function fixed')

# Verify still has cdDataBody
assert 'id=\"cdDataBody\"' in c, 'Frontend missing!'

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('ALL OK, size:', len(c))
