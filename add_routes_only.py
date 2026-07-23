import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 1. 只加后端路由（不带前端模板改动），最小化
routes = """

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
        if not row or not _verify(old_pw, row['password_hash']):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=?', uid)
        if not row or not _verify(old_pw, row['password_hash']):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=? WHERE id=?', _hash(new_pw), uid)
    return JSONResponse({'ok': True})

@app.post('/admin/user/{uid}/change_password')
async def admin_change_user_password(uid: int, request: Request):
    aid = _require(request)
    user = await _user(aid)
    if not user or user.get('role') != 'admin':
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
"""

# 找到 @app.get('/me') 后面插入
idx = c.find("@app.get('/me')")
after = c[idx:]
m = re.search(r'\n@app\.', after)
pos = idx + m.start() + 1
c = c[:pos] + routes + c[pos:]

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print(f'OK, {len(c)} bytes')
