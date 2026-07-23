import subprocess
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')

# 找到 loadUsers 里的 HTML 行模板
# 用户非admin的行：'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>'

# deleteUser 里的 HTML 行模板
# '<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>'

# 我要加：prompt改密码按钮 + 路由

# 1. 后端路由：在 get_me 之后，upload 之前加
# 当前 @app.post('/upload') 在 line 1026

# 2. UI 改两处：loadUsers 和 deleteUser 的表格行

# 计算增量
old_loadusers = """h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td></tr>'"""

new_loadusers = """h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+' <button onclick="var np=prompt(\'输入新密码(>4位)\');if(np&&np.length>=4){fetch(\'/admin/user/'+u.id+'/change_password\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({new_password:np}),credentials:\'include\'}).then(function(r){return r.json()}).then(function(d){alert(d.detail||\'成功\');loadUsers()})}else if(np){alert(\'密码需至少4位\')}" style="margin-left:5px">改密码</button><button style="margin-left:3px;cursor:pointer" onclick="var np=prompt(\'新密码(>4位)\');if(np&&np.length>=4){fetch(\'/admin/user/'+u.id+'/change_password\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({new_password:np}),credentials:\'include\'}).then(function(r){return r.json()}).then(function(d){alert(d.detail||\'成功\');loadUsers()})}else if(np){alert(\'需至少4位\')}">改密码</button>')+'</td></tr>'"""

print(f"Old loadUsers: {len(old_loadusers)} bytes")
print(f"New loadUsers: {len(new_loadusers)} bytes")
print(f"Delta: {len(new_loadusers) - len(old_loadusers)} bytes")
