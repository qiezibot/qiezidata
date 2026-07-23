# -*- coding: utf-8 -*-
c = open(r'C:\Users\lfy20\AppData\Local\Temp\full_utf8.py', 'r', encoding='utf-8').read()

# === Fix 1: deleteUser function - add password column ===
old_del = '''async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}'''

new_del = '''async function deleteUser(uid){try{var r=await fetch('/admin/user/'+uid,{method:'DELETE',credentials:'include'});if(r.ok){var r2=await fetch('/admin/users',{credentials:'include'});if(r2.status===401){window.location.href='/';return}var users=await r2.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\''+u.username+'\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}else{var e=await r.json();alert(e.detail||'删除失败')}}catch(e){alert('删除失败')}}'''

if old_del in c:
    c = c.replace(old_del, new_del)
    print('deleteUser patched')
else:
    print('deleteUser NOT FOUND in original, trying alternate encoding')
    # Try to find the function
    idx = c.find('async function deleteUser')
    if idx >= 0:
        snippet = c[idx:idx+1000]
        # Write snippet for analysis
        open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\_deleteUser_snippet.txt', 'w', encoding='utf-8').write(snippet)
        print(f'Found at {idx}, saved for analysis')

# === Fix 2: Add POST /me update route ===
# Find where the me route is and add after it
me_get = '''@app.get('/me')


async def get_me(request: Request):


    uid = _require(request); user = await _user(uid)


    if not user: raise HTTPException(status_code=404)


    return user'''

me_post = '''


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


    return JSONResponse({'ok': True})'''

if me_get in c:
    c = c.replace(me_get, me_get + me_post)
    print('POST /me added')
else:
    print('GET /me NOT FOUND')
    # Find approximate location
    idx = c.find('@app.get')
    routes = []
    while idx >= 0:
        end = c.find('\n\n\n@app', idx)
        if end < 0: end = c.find('\n\n\n\n@app', idx)
        if end < 0: break
        routes.append(c[idx:end])
        idx = c.find('@app.get', idx + 10)
    for r in routes:
        if '/me' in r[:100]:
            print('Found /me route variant:', r[:200])
            break

# === Fix 3: Add change password routes ===
change_routes = '''


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


    return JSONResponse({'ok': True, 'detail': '密码已修改'})'''

# Insert change password routes after get_me
me_block_end = c.find('\n\n\n@app', c.find('def get_me'))
c = c[:me_block_end] + change_routes + c[me_block_end:]
print('Change password routes added')

# === Fix 4: Update _ADMIN template ===
adm_start = c.find('_ADMIN =')
adm_end = c.find('"""', adm_start + 10)
adm = c[adm_start:adm_end]

# 4a. User table: add password column header
old_th = '<th>ID</th><th>用户名为</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th>'
if old_th in adm:
    new_th = '<th>ID</th><th>用户名为</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th><th>修改密码</th>'
    adm = adm.replace(old_th, new_th)
    print('4a. User table header updated')
else:
    print('4a. User table header NOT FOUND, checking actual content...')
    # Find the actual header
    idx = adm.find('<th>ID</th>')
    if idx >= 0:
        print('Actual header:', adm[idx:idx+200])

# 4b. Add password modal
close_pos = adm.find('</div>', adm.find('page-clouddata'))
# Find page-users closing div precisely
pu_start = adm.find('page-users')
depth = 0
pu_close = -1
for i in range(pu_start, len(adm)):
    if adm[i:i+4] == '<div': depth += 1
    elif adm[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            pu_close = i + 6
            break
print(f'page-users closes at {pu_close}')

modal = '''

<div id="pwdModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:1000;align-items:center;justify-content:center">
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
</div>

'''

adm = adm[:pu_close] + modal + adm[pu_close:]
print('4b. Password modal added')

# 4c. Add profile page after page-upload
upload_start = adm.find('page-upload')
depth = 0
upload_close = -1
for i in range(upload_start, len(adm)):
    if adm[i:i+4] == '<div': depth += 1
    elif adm[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            upload_close = i + 6
            break
print(f'page-upload closes at {upload_close}')

profile_page = '''

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

'''

adm = adm[:upload_close] + profile_page + adm[upload_close:]
print('4c. Profile page added')

# 4d. Add profile nav item
old_nav = '<div class="nav-item" onclick="switchPage(\'apidocs\',this)"><span class="icon">'
new_nav = '<div class="nav-item" onclick="switchPage(\'profile\',this)"><span class="icon">&#x1f464;</span>个人资料</div>\n\n\n<div class="nav-item" onclick="switchPage(\'apidocs\',this)"><span class="icon">'
adm = adm.replace(old_nav, new_nav)
print('4d. Profile nav item added')

# 4e. Update loadUsers to include password column
old_lu = '''function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}'''

new_lu = '''function loadUsers(){try{var r=await fetch('/admin/users',{credentials:'include'});if(r.status===401){window.location.href='/';return}var users=await r.json();var h='';for(var i=0;i<users.length;i++){var u=users[i];h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style="color:green">已是管理员</span>':'<button data-uid="'+u.id+'" data-uname="'+u.username+'" class="del-btn">删除</button><button data-uid="'+u.id+'" data-uname="'+u.username+'" class="set-admin-btn" style="margin-left:5px">设为管理员</button>')+'</td>'+'<td><button onclick="openPwdModal('+u.id+',\''+u.username+'\')" style="padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer">修改密码</button></td></tr>'}document.getElementById('userTableBody').innerHTML=h}catch(e){}}'''

if old_lu in adm:
    adm = adm.replace(old_lu, new_lu)
    print('4e. loadUsers updated')
else:
    print('4e. loadUsers NOT FOUND, searching...')
    idx = adm.find('function loadUsers')
    if idx >= 0:
        print('Found at', idx, '- character length:', len(adm[idx:adm.find('}catch(e){}}', idx)+12]))
        print('Snippet:', repr(adm[idx:idx+200]))

# 4f. Update deleteUser in adm (rebuild rows)
if 'async function deleteUser' in adm:
    idx = adm.find('async function deleteUser')
    # Get the full function
    fun_end = adm.find(')', idx + 100)
    fun_end = adm.find('}', fun_end)
    # Find the specific row rebuild pattern
    rebuild_start = adm.find("h+='<tr><td>'", idx)
    rebuild_end = adm.find("document.getElementById('userTableBody').innerHTML=h", idx)
    old_row = adm[rebuild_start:rebuild_end]
    new_row = old_row.replace("'</td></tr>'", "'</td>'+'<td><button onclick=\"openPwdModal('+u.id+',\\''+u.username+'\\')\" style=\"padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer\">修改密码</button></td></tr>'")
    if old_row != new_row:
        adm = adm[:rebuild_start] + new_row + adm[rebuild_end:]
        print('4f. deleteUser rebuild rows updated')
    else:
        print('4f. deleteUser row pattern not changed')
else:
    print('4f. deleteUser not in adm')

# 4g. Add JS functions for modal and profile
last_script = adm.rfind('<script>')
new_js = '''
<script>
// Password modal functions
var pwdModalTargetUid = null;
var pwdModalTargetName = '';
function openPwdModal(uid, uname){ pwdModalTargetUid = uid; pwdModalTargetName = uname; document.getElementById('pwdModalTitle').textContent = '修改密码 - ' + uname; document.getElementById('pwdNewInput').value = ''; document.getElementById('pwdConfirmInput').value = ''; document.getElementById('pwdModalMsg').style.display = 'none'; document.getElementById('pwdModal').style.display = 'flex'; }
function closePwdModal(){ document.getElementById('pwdModal').style.display = 'none'; pwdModalTargetUid = null; }
function submitPwdModal(){ var np = document.getElementById('pwdNewInput').value; var cp = document.getElementById('pwdConfirmInput').value; var msg = document.getElementById('pwdModalMsg'); if(np.length < 4){ msg.textContent = '密码至少4个字符'; msg.style.display = 'block'; return; } if(np !== cp){ msg.textContent = '两次输入的密码不一致'; msg.style.display = 'block'; return; } document.getElementById('pwdModalBtn').disabled = true; document.getElementById('pwdModalBtn').textContent = '提交中...'; fetch('/admin/user/' + pwdModalTargetUid + '/change_password', { method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({new_password: np}) }).then(function(r){ return r.json(); }).then(function(d){ if(d.ok){ alert('密码已修改'); closePwdModal(); } else { msg.textContent = d.detail || '修改失败'; msg.style.display = 'block'; } }).catch(function(){ msg.textContent = '请求失败'; msg.style.display = 'block'; }).finally(function(){ document.getElementById('pwdModalBtn').disabled = false; document.getElementById('pwdModalBtn').textContent = '确认修改'; }); }
// Profile functions
function loadProfile(){ fetch('/me', {credentials:'include'}).then(function(r){ return r.json(); }).then(function(u){ document.getElementById('profileUsername').value = u.username || ''; document.getElementById('profileDisplayName').value = u.display_name || ''; document.getElementById('profileRole').value = u.role || ''; }).catch(function(){}); }
function saveProfile(){ var dn = document.getElementById('profileDisplayName').value.trim(); var msg = document.getElementById('profileSaveMsg'); fetch('/me', { method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({display_name: dn}) }).then(function(r){ return r.json(); }).then(function(d){ if(d.ok){ msg.textContent = '已保存'; msg.style.color = '#27ae60'; } else { msg.textContent = d.detail || '保存失败'; msg.style.color = '#e74c3c'; } msg.style.display = 'block'; setTimeout(function(){ msg.style.display = 'none'; }, 3000); }).catch(function(){ msg.textContent = '请求失败'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; }); }
function submitProfilePwd(){ var oldP = document.getElementById('profileOldPwd').value; var newP = document.getElementById('profileNewPwd').value; var newP2 = document.getElementById('profileNewPwd2').value; var msg = document.getElementById('profilePwdMsg'); if(!oldP){ msg.textContent = '请输入旧密码'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; } if(newP.length < 4){ msg.textContent = '新密码至少4个字符'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; } if(newP !== newP2){ msg.textContent = '两次输入的密码不一致'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; return; } fetch('/me/change_password', { method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({old_password: oldP, new_password: newP}) }).then(function(r){ return r.json(); }).then(function(d){ if(d.ok){ msg.textContent = '密码已修改'; msg.style.color = '#27ae60'; document.getElementById('profileOldPwd').value = ''; document.getElementById('profileNewPwd').value = ''; document.getElementById('profileNewPwd2').value = ''; } else { msg.textContent = d.detail || '修改失败'; msg.style.color = '#e74c3c'; } msg.style.display = 'block'; setTimeout(function(){ msg.style.display = 'none'; }, 3000); }).catch(function(){ msg.textContent = '请求失败'; msg.style.color = '#e74c3c'; msg.style.display = 'block'; }); }
// Extend switchPage
(function(){ var orig = window.switchPage; if(orig){ window.switchPage = function(page, el){ orig(page, el); if(page === 'profile') loadProfile(); }; } })();
</script>
'''

adm = adm[:last_script] + new_js + adm[last_script:]
print('4g. JS functions added')

# Write final output
c = c[:adm_start] + adm + c[adm_end:]
out = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py'
open(out, 'w', encoding='utf-8').write(c)
print('\nWritten to', out)
print('Done!')
