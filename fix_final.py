# -*- coding: utf-8 -*-
c = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'r', encoding='utf-8').read()

# Find the JS block that contains loadUsers, deleteUser, events
lu_start = c.find('function loadUsers')
lu_end = c.find('async function loadMyFiles')

print(f"Replacing block {lu_start} -> {lu_end}")
old_block = c[lu_start:lu_end]

# Build NEW loadUsers + deleteUser + event handlers
# Use raw JS that we'll generate cleanly
new_functions = """
function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\\''+u.username+'\\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}
document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.del-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定要删除用户'+uname+'?此操作不可恢复'))deleteUser(uid)})
document.getElementById('userTableBody').addEventListener('click',function(e){var btn=e.target.closest('.set-admin-btn');if(!btn)return;var uid=parseInt(btn.getAttribute('data-uid'));var uname=btn.getAttribute('data-uname');if(confirm('确定将用户'+uname+'设为管理员吗?')){fetch('/admin/user/'+uid+'/set_admin',{method:'POST',credentials:'include'}).then(function(r){if(r.ok){alert('已设为管理员');loadUsers()}else{r.json().then(function(d){alert(d.detail||'设置失败')})}}).catch(function(){alert('请求失败')})}})
async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\\''+u.username+'\\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}
"""

c = c[:lu_start] + new_functions + c[lu_end:]

# Also fix the table header - "用户名" and "操作" columns
# Find the actual header row in the HTML
hdr_start = c.find('<th>ID</th>')
if hdr_start > 0:
    hdr_end = c.find('</thead>', hdr_start)
    old_hdr = c[hdr_start:hdr_end]
    print(f"Header found: {hdr_start}")
    print(f"Old header: {repr(old_hdr)}")
    
    # The header is: <th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th>
    # We need to add <th>修改密码</th>
    new_hdr = old_hdr.replace('</th></tr>', '</th><th>修改密码</th></tr>')
    # More specific: find '</th><th>操作</th></tr>'
    if '</th><th>' in old_hdr:
        # Split at last th before </tr>
        parts = old_hdr.rsplit('</th>', 2)
        if len(parts) >= 2:
            # parts[-2] is the last cell, parts[-1] has the </tr>
            new_hdr = parts[0] + '</th><th>操作</th><th>修改密码</th>' + parts[-1]
            print(f"New header: {repr(new_hdr)}")

    c = c[:hdr_start] + new_hdr + c[hdr_end:]

# Check POST /me exists
if 'def update_me' not in c:
    print("POST /me still missing, adding it...")
    get_me_end = c.find('return user', c.find('def get_me')) + 11
    post_me = """

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


    return JSONResponse({'ok': True})"""
    
    c = c[:get_me_end] + '\n\n' + post_me + c[get_me_end:]

# Save
out = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py'
open(out, 'w', encoding='utf-8').write(c)
print(f"Written! {len(c)} bytes")
print("Contains '修改密码':", '修改密码' in c)
print("Contains 'openPwdModal':", 'openPwdModal' in c)
print("Contains 'def update_me':", 'def update_me' in c)
print("Contains 'change_password':", 'change_password' in c)
print("Contains 'page-profile':", 'page-profile' in c)
