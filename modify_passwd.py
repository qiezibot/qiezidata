# -*- coding: utf-8 -*-
"""
修改 railway_file_server.py 加入修改密码功能：
1. 用户管理：每行加"修改密码"按钮（弹窗输入新密码）
2. 个人资料页面：显示当前用户信息 + 修改密码表单
"""

c = open(r'C:\Users\lfy20\AppData\Local\Temp\full_utf8.py', 'r', encoding='utf-8').read()

# ========== 1. 后端路由：修改密码 API ==========

# 在 /me 路由后面加一个 change_password 路由
me_route = """
@app.get('/me')


async def get_me(request: Request):


    uid = _require(request); user = await _user(uid)


    if not user: raise HTTPException(status_code=404)


    return user
"""

change_pwd_route = """
@app.post('/me/change_password')


async def change_my_password(request: Request):


    uid = _require(request)


    data = await request.json()


    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')


    if not new_pw or len(new_pw) < 4:


        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})


    # 验证旧密码


    if use_pg:


        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=$1', uid)


    else:


        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=?', uid)


    if not row or not _verify(old_pw, row['password_hash']):


        return JSONResponse({'ok': False, 'detail': '旧密码错误'})


    new_hash = _hash(new_pw)


    if use_pg:


        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', new_hash, uid)


    else:


        await db_execute('UPDATE users SET password_hash=? WHERE id=?', new_hash, uid)


    return JSONResponse({'ok': True, 'detail': '密码已修改'})


@app.post('/admin/user/{uid}/change_password')


async def admin_change_user_password(uid: int, request: Request):


    aid = _require(request); user = await _user(aid)


    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)


    data = await request.json()


    new_pw = data.get('new_password', '')


    if not new_pw or len(new_pw) < 4:


        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})


    if use_pg:


        row = await db_fetchrow('SELECT id FROM users WHERE id=$1', uid)


    else:


        row = await db_fetchrow('SELECT id FROM users WHERE id=?', uid)


    if not row:


        return JSONResponse({'ok': False, 'detail': '用户不存在'})


    new_hash = _hash(new_pw)


    if use_pg:


        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', new_hash, uid)


    else:


        await db_execute('UPDATE users SET password_hash=? WHERE id=?', new_hash, uid)


    return JSONResponse({'ok': True, 'detail': '密码已修改'})
"""

c = c.replace(me_route, me_route + '\n\n' + change_pwd_route)
print('1. Added /me/change_password and /admin/user/{uid}/change_password routes')

# ========== 2. _ADMIN 模板修改 ==========

adm_start = c.find('_ADMIN =')
adm_end = c.find('"""', adm_start + 10)
adm = c[adm_start:adm_end]

# 2a. 在用户管理表格加"修改密码"列
old_user_table = '<th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th>'
new_user_table = '<th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th><th>修改密码</th>'
adm = adm.replace(old_user_table, new_user_table)

# 2b. 在用户管理页面加一个修改密码的modal弹窗，放在page-users的</div>之前
page_users_close = adm.rfind('</div>', adm.find('page-users'), adm.find('page-clouddata'))
# Find the closing of page-users tab-page
page_users_start = adm.find('page-users')
page_users_closing = adm.find('</div>', adm.find('</table>', page_users_start))
page_users_closing = adm.find('</div>', page_users_closing + 1)  # close card div
page_users_closing = adm.find('</div>', page_users_closing + 1)  # close tab-page div

# Actually find the exact closing div for page-users
pu_div_start = adm.find('class="tab-page" id="page-users"')
# Find the matching closing div - it's the div at the same nesting level
# Count div opens and closes
depth = 0
close_pos = -1
for i in range(pu_div_start, len(adm)):
    if adm[i:i+4] == '<div':
        depth += 1
    elif adm[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            close_pos = i + 6
            break

print(f'page-users div closes at {close_pos}')

# Insert modal + change password column logic before the page-users closing
modal_html = """
\n\n<div id="pwdModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center">
<div style="background:#fff;border-radius:12px;padding:24px;width:360px;max-width:90%;box-shadow:0 10px 40px rgba(0,0,0,.3)">
<h3 id="pwdModalTitle" style="margin:0 0 16px 0;font-size:16px;color:#333">修改密码</h3>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">新密码</label><input id="pwdNewInput" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="至少4个字符" required></div>
<div class="input-group" style="margin-bottom:16px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">确认新密码</label><input id="pwdConfirmInput" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="再次输入新密码" required></div>
<p id="pwdModalMsg" style="color:#e74c3c;font-size:13px;margin:0 0 12px 0;display:none"></p>
<div style="display:flex;gap:8px;justify-content:flex-end">
<button onclick="closePwdModal()" style="padding:8px 20px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;font-size:14px">取消</button>
<button id="pwdModalBtn" onclick="submitPwdModal()" style="padding:8px 20px;background:#667eea;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">确认修改</button>
</div>
</div>
</div>\n\n"""

adm = adm[:close_pos] + modal_html + adm[close_pos:]
print('2a. Added password modal')

# 2c. Add "profile" tab page after page-upload
profile_page = """
<div class="tab-page" id="page-profile">
<div class="card"><h2>个人资料</h2>
<div style="max-width:400px">
<div class="input-group"><label>用户名</label><input id="profileUsername" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9" readonly></div>
<div class="input-group"><label>显示名称</label><input id="profileDisplayName" type="text" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入显示名称"></div>
<div class="input-group"><label>角色</label><input id="profileRole" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9" readonly></div>
<button onclick="saveProfile()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;margin-top:4px">保存</button>
<p id="profileSaveMsg" style="font-size:13px;margin-top:8px;display:none"></p>
</div>
</div>
<div class="card"><h2>修改密码</h2>
<div style="max-width:400px">
<div class="input-group"><label>旧密码</label><input id="profileOldPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入当前密码"></div>
<div class="input-group"><label>新密码</label><input id="profileNewPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="至少4个字符"></div>
<div class="input-group"><label>确认新密码</label><input id="profileNewPwd2" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="再次输入新密码"></div>
<button onclick="submitProfilePwd()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;margin-top:4px">修改密码</button>
<p id="profilePwdMsg" style="font-size:13px;margin-top:8px;display:none"></p>
</div>
</div>
</div>

"""

# Insert after page-upload's closing div
upload_start = adm.find('page-upload')
# Find upload's closing div
depth = 0
upload_close = -1
for i in range(upload_start, len(adm)):
    if adm[i:i+4] == '<div':
        depth += 1
    elif adm[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            upload_close = i + 6
            break

print(f'page-upload closes at {upload_close}')
adm = adm[:upload_close] + profile_page + adm[upload_close:]
print('2b. Added profile page')

# 2d. Add "个人资料" nav item in sidebar, before "API文档"
old_nav_apidocs = '<div class="nav-item" onclick="switchPage(\'apidocs\',this)">'
new_nav_profile = '<div class="nav-item" onclick="switchPage(\'profile\',this)"><span class="icon">&#x1f464;</span>个人资料</div>\n\n'
adm = adm.replace(old_nav_apidocs, new_nav_profile + old_nav_apidocs)
print('2c. Added profile nav item')

# 2e. Modify JS: loadUsers function - add change password column
old_loadusers = """function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}"""

new_loadusers = """function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\''+u.username+'\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}"""

adm = adm.replace(old_loadusers, new_loadusers)
print('2d. Updated loadUsers with password column')

# Also update the deleteUser function which rebuilds rows
old_deleteUser_rebuild = """async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}"""

new_deleteUser_rebuild = """async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\''+u.username+'\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}"""

if old_deleteUser_rebuild in adm:
    adm = adm.replace(old_deleteUser_rebuild, new_deleteUser_rebuild)
    print('2e. Updated deleteUser rebuild with password column')
else:
    print('2e. deleteUser function not found in expected form, trying shorter match')

# 2f. Add new JS functions - openPwdModal, closePwdModal, submitPwdModal
# Insert before the last </script>
last_script_close = adm.rfind('</script>')
# Actually we want to insert new JS BEFORE the last inline script that hides nav items
# Find the last <script> opening
last_script_open = adm.rfind('<script>')

new_js_functions = """
<script>
// Password modal for admin user management
var pwdModalTargetUid = null;
var pwdModalTargetName = '';
function openPwdModal(uid, uname){
  pwdModalTargetUid = uid;
  pwdModalTargetName = uname;
  document.getElementById('pwdModalTitle').textContent = '修改密码 - ' + uname;
  document.getElementById('pwdNewInput').value = '';
  document.getElementById('pwdConfirmInput').value = '';
  document.getElementById('pwdModalMsg').style.display = 'none';
  document.getElementById('pwdModal').style.display = 'flex';
}
function closePwdModal(){
  document.getElementById('pwdModal').style.display = 'none';
}
function submitPwdModal(){
  var np = document.getElementById('pwdNewInput').value;
  var cp = document.getElementById('pwdConfirmInput').value;
  if(np.length < 4){ document.getElementById('pwdModalMsg').textContent = '密码至少4个字符'; document.getElementById('pwdModalMsg').style.display = 'block'; return; }
  if(np !== cp){ document.getElementById('pwdModalMsg').textContent = '两次输入的密码不一致'; document.getElementById('pwdModalMsg').style.display = 'block'; return; }
  document.getElementById('pwdModalBtn').disabled = true;
  document.getElementById('pwdModalBtn').textContent = '提交中...';
  fetch('/admin/user/' + pwdModalTargetUid + '/change_password', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({new_password: np})
  }).then(function(r){ return r.json(); }).then(function(d){
    if(d.ok){
      alert('密码已修改');
      closePwdModal();
    } else {
      document.getElementById('pwdModalMsg').textContent = d.detail || '修改失败';
      document.getElementById('pwdModalMsg').style.display = 'block';
    }
  }).catch(function(){
    document.getElementById('pwdModalMsg').textContent = '请求失败';
    document.getElementById('pwdModalMsg').style.display = 'block';
  }).finally(function(){
    document.getElementById('pwdModalBtn').disabled = false;
    document.getElementById('pwdModalBtn').textContent = '确认修改';
  });
}
// Profile page
function loadProfile(){
  fetch('/me', {credentials:'include'}).then(function(r){ return r.json(); }).then(function(u){
    document.getElementById('profileUsername').value = u.username || '';
    document.getElementById('profileDisplayName').value = u.display_name || '';
    document.getElementById('profileRole').value = u.role || '';
  });
}
function saveProfile(){
  var dn = document.getElementById('profileDisplayName').value.trim();
  fetch('/me', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({display_name: dn})
  }).then(function(r){ return r.json(); }).then(function(d){
    var msg = document.getElementById('profileSaveMsg');
    if(d.ok){
      msg.textContent = '已保存';
      msg.style.color = '#27ae60';
    } else {
      msg.textContent = d.detail || '保存失败';
      msg.style.color = '#e74c3c';
    }
    msg.style.display = 'block';
    setTimeout(function(){ msg.style.display = 'none'; }, 3000);
  });
}
function submitProfilePwd(){
  var oldP = document.getElementById('profileOldPwd').value;
  var newP = document.getElementById('profileNewPwd').value;
  var newP2 = document.getElementById('profileNewPwd2').value;
  var msg = document.getElementById('profilePwdMsg');
  if(!oldP){ msg.textContent = '请输入旧密码'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; }
  if(newP.length < 4){ msg.textContent = '新密码至少4个字符'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; }
  if(newP !== newP2){ msg.textContent = '两次输入的密码不一致'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; }
  fetch('/me/change_password', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({old_password: oldP, new_password: newP})
  }).then(function(r){ return r.json(); }).then(function(d){
    if(d.ok){
      msg.textContent = '密码已修改';
      msg.style.color = '#27ae60';
      document.getElementById('profileOldPwd').value = '';
      document.getElementById('profileNewPwd').value = '';
      document.getElementById('profileNewPwd2').value = '';
    } else {
      msg.textContent = d.detail || '修改失败';
      msg.style.color = '#e74c3c';
    }
    msg.style.display = 'block';
    setTimeout(function(){ msg.style.display = 'none'; }, 3000);
  }).catch(function(){
    msg.textContent = '请求失败';
    msg.style.color = '#e74c3c';
    msg.style.display = 'block';
  });
}
// Extend switchPage to load profile when shown
var origSwitchPage = window.switchPage;
window.switchPage = function(page, el){
  if(typeof origSwitchPage === 'function') origSwitchPage(page, el);
  if(page === 'profile') loadProfile();
};
</script>
"""

adm = adm[:last_script_open] + new_js_functions + adm[last_script_open:]
print('2f. Added password modal and profile JS functions')

# 2g. Add POST /me route for updating display_name
me_post_route = """
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

c = c.replace(me_route, me_route + '\n\n' + change_pwd_route + '\n\n' + me_post_route)
print('3. Added POST /me for updating display_name')

# Now replace the _ADMIN template
c = c[:adm_start] + adm + c[adm_end:]
print('4. Replaced _ADMIN template')

# Write output
out_path = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py'
open(out_path, 'w', encoding='utf-8').write(c)
print('5. Written to:', out_path)
print('Done!')
