import subprocess
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')

# 方案：加一个全局函数 cpwUser(uid)，表格行只加 onclick 调用
# 函数定义一次约 280 字节，每处引用加约 30 字节
# 两处引用：loadUsers + deleteUser = 30*2 + 280 = 340 字节
# 后端路由：约 400 字节
# 总计增量：~740 字节 → 85804 + 740 = 86544 = 84.5KB → 应该可以

# 更精简方案：函数定义写在一行
fn_def = "function cpwUser(uid){var np=prompt('新密码(>4位)');if(!np){return}if(np.length<4){alert('需>=4字符');return}fetch('/admin/user/'+uid+'/change_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np}),credentials:'include'}).then(function(r){return r.json()}).then(function(d){alert(d.detail||'成功');loadUsers()})}"
print(f"Function def: {len(fn_def)} bytes")

# 后端路由
route = "\n@app.post('/admin/user/{uid}/change_password')\nasync def cpw_admin(uid: int, request: Request):\n    await _require_admin(request)\n    data = await request.json()\n    np = data.get('new_password', '')\n    if not np or len(np) < 4:\n        return JSONResponse({'ok': False, 'detail': '密码需至少4个字符'})\n    if use_pg:\n        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(np), uid)\n    else:\n        _DB[uid]['password_hash'] = _hash(np)\n    return JSONResponse({'ok': True, 'detail': '密码已修改'})"
print(f"Route: {len(route)} bytes")

# deleteUser 里的行模板 - 原版
old_del = "<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>"
# 新版 - 加改密码按钮
new_del = "<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button><button onclick=\"cpwUser('+u.id+')\" style=\"margin-left:5px;cursor:pointer\">改密码</button>"
print(f"Old deleteUser row: {len(old_del)}")
print(f"New deleteUser row: {len(new_del)}")
print(f"Delta deleteUser: {len(new_del)-len(old_del)}")

# loadUsers 里也是加同样的按钮
# 但是 admin 行不变，非 admin 行加在 set-admin-btn 后面
old_lu_admin_buttons = "<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">设为管理员</button>"
new_lu_admin_buttons = "<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">设为管理员</button><button onclick=\"cpwUser('+u.id+')\" style=\"margin-left:5px;cursor:pointer\">改密码</button>"
print(f"Old loadUsers buttons: {len(old_lu_admin_buttons)}")
print(f"New loadUsers buttons: {len(new_lu_admin_buttons)}")
print(f"Delta loadUsers: {len(new_lu_admin_buttons)-len(old_lu_admin_buttons)}")

print(f"\nTotal delta: {len(route) + len(fn_def) + (len(new_lu_admin_buttons)-len(old_lu_admin_buttons)) + (len(new_del)-len(old_del))}")
print(f"New total size: {85804 + len(route) + len(fn_def) + (len(new_lu_admin_buttons)-len(old_lu_admin_buttons)) + (len(new_del)-len(old_del))}")
