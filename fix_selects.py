# Fix script clouddata APIs: use db_fetchrow/db_fetch for SELECT, not db_execute
with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fixes needed:
# script_cd_list: use db_fetchrow for single, db_fetch for list
# script_cd_get: use db_fetchrow
# script_cd_export: use db_fetch

import re

# Fix script_cd_list
old_list_func = content[content.find('async def script_cd_list'):content.find('async def script_cd_get')]
new_list_func = '''async def script_cd_list(request: Request, key: str = None):
    _require(request)
    if key:
        r = await db_fetchrow('SELECT k,v,t,read FROM clouddata WHERE k=$1' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE k=?', key)
        if r:
            return {'key':r['k'],'value':r['v'],'time':str(r['t']),'read':r['read']}
        return {'error':'not found'}
    r = await db_fetch('SELECT k,v,t,read FROM clouddata ORDER BY id DESC' if use_pg else 'SELECT k,v,t,read FROM clouddata ORDER BY id DESC')
    return [{'key':x['k'],'value':x['v'],'time':str(x['t']) if x['t'] else '','read':x['read']} for x in r]

'''

# For script_cd_get
old_get_func = content[content.find('async def script_cd_get'):content.find('async def script_cd_delete')]
new_get_func = '''async def script_cd_get(key: str, request: Request):
    _require(request)
    r = await db_fetchrow('SELECT k,v,t,read FROM clouddata WHERE k=$1' if use_pg else 'SELECT k,v,t,read FROM clouddata WHERE k=?', key)
    if not r: raise HTTPException(404, 'key not found')
    return {'key':r['k'],'value':r['v'],'time':str(r['t']),'read':r['read']}

'''

# Fix script_cd_export
old_export_func = content[content.find('async def script_cd_export'):content.find('async def script_cd_mark')]
new_export_func = '''async def script_cd_export(mode: str, request: Request):
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

'''

content = content.replace(old_list_func, new_list_func, 1)
content = content.replace(old_get_func, new_get_func, 1)
content = content.replace(old_export_func, new_export_func, 1)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Size: {len(content)} bytes")
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")

# Verify all functions
for fn in ['script_cd_list', 'script_cd_get', 'script_cd_export']:
    cnt = content.count('async def ' + fn)
    print(f"  {fn}: {cnt}")
