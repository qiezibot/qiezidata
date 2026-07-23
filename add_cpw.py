with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()

# 1. 在 get_me 和 /upload 之间加 change_password 路由
old = "@app.get('/me')\nasync def get_me(request: Request):\n    uid = _require(request); user = await _user(uid)\n    if not user: raise HTTPException(status_code=404)\n    return user\n\n@app.post('/upload')"
new = "@app.get('/me')\nasync def get_me(request: Request):\n    uid = _require(request); user = await _user(uid)\n    if not user: raise HTTPException(status_code=404)\n    return user\n\n@app.post('/admin/user/{uid}/change_password')\nasync def cpw_admin(uid: int, request: Request):\n    admin = await _user(_require(request))\n    if not admin or admin.get('role') != 'admin':\n        return JSONResponse({'ok': False, 'detail': '无权限'})\n    data = await request.json()\n    np = data.get('new_password', '')\n    if not np or len(np) < 4:\n        return JSONResponse({'ok': False, 'detail': '密码需至少4个字符'})\n    if use_pg:\n        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(np), uid)\n    else:\n        conn = sqlite3.connect('/data/files.db')\n        conn.execute('UPDATE users SET password_hash=? WHERE id=?', (_hash(np), uid))\n        conn.commit(); conn.close()\n    return JSONResponse({'ok': True, 'detail': '密码已修改'})\n\n@app.post('/upload')"
c = c.replace(old, new, 1)
print("1. Added change_password route ✅")

# 2. 在 loadUsers 前加 cpwUser 函数
# loadUsers 行：async function loadUsers(){try...
old_lu = "async function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}"

cpw_fn = "function cpwUser(uid){var np=prompt('新密码(>4位)');if(!np||np.length<4){if(np)alert('需>=4字符');return}fetch('/admin/user/'+uid+'/change_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np}),credentials:'include'}).then(function(r){return r.json()}).then(function(d){alert(d.detail||'成功');loadUsers()})}"
new_lu = cpw_fn + "\n" + old_lu
c = c.replace(old_lu, new_lu, 1)
print("2. Added cpwUser function ✅")

# 3. 在 loadUsers 表格行加改密码按钮（每个用户行）
# 就是在 </td></tr> 前加按钮
old_row = "'<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td></tr>'"
new_row = "'<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td><td><button onclick=\"cpwUser('+u.id+')\" style=\"cursor:pointer\">改密码</button></td></tr>'"
c = c.replace(old_row, new_row, 1)
print("3. Added password button to user rows ✅")

with open('railway_file_server.py','w',encoding='utf-8') as f:
    f.write(c)

sz = len(c.encode('utf-8'))
print(f"\nFinal size: {sz} bytes")
cpw_count = c.count('cpwUser')
print(f"cpwUser refs: {cpw_count} (expect 2: function def + button)")
route_ok = '/change_password' in c
print(f"change_password route: {route_ok}")
