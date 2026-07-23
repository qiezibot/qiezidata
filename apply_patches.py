# -*- coding: utf-8 -*-
"""
Direct byte-level patching of railway_file_server.py (original from GitHub).
Surgical inserts using exact byte offsets.
"""
raw = open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_original.py', 'rb').read()
text = raw.decode('utf-8')

patches = []

print(f"Total file size: {len(text)}")

# ===== 1. Backend: Add /me/change_password route =====
get_me_func = text.find("@app.get('/me')")
get_me_end = text.find('\n\n\n@app', get_me_func + 1)
print(f"GET /me block: {get_me_func} to {get_me_end}")

change_pwd = r"""


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


    return JSONResponse({'ok': True})


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


    return JSONResponse({'ok': True})"""

patches.append((get_me_end, change_pwd))
print("1. Route patches queued")

# ===== 2. Frontend: Update _ADMIN template =====
adm_start = text.find('_ADMIN = """')
if text[adm_start + 11:adm_start + 14] == '"""':
    adm_start_content = adm_start + 14  # _ADMIN = """ 
else:
    adm_start_content = adm_start + 12  # _ADMIN = """

adm_end_marker = '"""\n\n\n\n\n\n\n\n\n\n\n\n\n# ---- CloudData Project API ----'
adm_end = text.find(adm_end_marker, adm_start_content)
print(f"ADMIN content: {adm_start_content} to {adm_end}")

adm = text[adm_start_content:adm_end]
print(f"ADMIN content length: {len(adm)}")

# 2a. Add password column header to user table
old_header = '<th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th>'
new_header = '<th>ID</th><th>用户名</th><th>显示名称</th><th>角色</th><th>创建时间</th><th>操作</th><th>修改密码</th>'
if old_header in adm:
    adm = adm.replace(old_header, new_header)
    print("2a. Table header updated")

# 2b. Add password column to loadUsers
old_lu = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style=\"color:green\">已是管理员</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">设为管理员</button>')+'</td></tr>'"
new_lu = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style=\"color:green\">已是管理员</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">设为管理员</button>')+'</td>'+'<td><button onclick=\"openPwdModal('+u.id+')\" style=\"padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer\">修改密码</button></td></tr>'"
if old_lu in adm:
    adm = adm.replace(old_lu, new_lu)
    print("2b. loadUsers updated")

# 2c. Add password column to deleteUser rebuild
old_del = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>')+'</td></tr>'"
new_del = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">删除</button>')+'</td>'+'<td><button onclick=\"openPwdModal('+u.id+')\" style=\"padding:4px 10px;font-size:12px;border:1px solid #ddd;border-radius:6px;color:#555;background:#fff;cursor:pointer\">修改密码</button></td></tr>'"
if old_del in adm:
    adm = adm.replace(old_del, new_del)
    print("2c. deleteUser updated")

# 2d. Modify sidebar bottom: make username clickable
# Original: <span>&#x1f464; <!--U--></span> &middot; <a href="/logout">退出登录</a>
# New: <a onclick="openProfile()" style="cursor:pointer">&#x1f464; <!--U--></a> &middot; <a href="/logout">退出登录</a>
old_bottom = '<span>&#x1f464; <!--U--></span> &middot; <a href="/logout">\u9000\u51fa\u767b\u5f55</a>'
new_bottom = '<a onclick="openProfile()" style="cursor:pointer">&#x1f464; <!--U--></a> &middot; <a href="/logout">\u9000\u51fa\u767b\u5f55</a>'
if old_bottom in adm:
    adm = adm.replace(old_bottom, new_bottom)
    print("2d. Sidebar username made clickable")
else:
    # Try with unicode chars
    idx = adm.find('<span>&#x1f464;')
    if idx > 0:
        before = adm[idx:idx+120]
        print(f"  Bottom area not matched, found: {repr(before)}")

# Also make top header username clickable
old_top = '<span class="user-area">&#x1f464; <!--U--></span>'
new_top = '<span class="user-area"><a onclick="openProfile()" style="cursor:pointer;color:inherit;text-decoration:none">&#x1f464; <!--U--></a></span>'
if old_top in adm:
    adm = adm.replace(old_top, new_top)
    print("2e. Top header username made clickable")
else:
    idx = adm.find('user-area')
    if idx > 0:
        print(f"  Top area: {repr(adm[idx:idx+80])}")

# 2f. Remove profile nav item (if exists) from sidebar
# Also remove the profile tab-page slot from the old code if it exists
profile_nav_pattern = '<div class="nav-item" onclick="switchPage(\'profile\',this)"><span class="icon">&#x1f464;</span>个人资料</div>'
profile_tab_page = '<div class="tab-page" id="page-profile">'
profile_tab_end = '</div>\n\n\n</div>\n\n\n\n<div class="tab-page" id="page-users">'

# Check if profile tab page exists in our modified version
if profile_tab_page in adm:
    # Remove the entire profile tab page
    pp_start = adm.find(profile_tab_page)
    pp_end = adm.find('<div class="tab-page" id="page-users">', pp_start)
    if pp_end > 0:
        # Remove everything from profile page start to before page-users
        adm = adm[:pp_start] + adm[pp_end:]
        print("2f. Profile tab page removed")
    else:
        print("2f. Could not find page-users after profile page")

# Remove profile nav item
if profile_nav_pattern in adm:
    adm = adm.replace(profile_nav_pattern, '')
    print("2g. Profile nav item removed")

# 2h. Add profile modal after the password modal area
pwd_modal = '<div id="pwdModal" style="display:none;'
profile_modal = """

<div id="profileModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center">
<div style="background:#fff;border-radius:12px;padding:24px;width:420px;max-width:90%;box-shadow:0 10px 40px rgba(0,0,0,.3)">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
<h3 style="margin:0;font-size:16px;color:#333">修改资料</h3><button onclick="closeProfile()" style="background:none;border:none;font-size:20px;cursor:pointer;color:#999">&times;</button>
</div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">用户名</label><input id="profModalUser" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">显示名称</label><input id="profModalDN" type="text" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入显示名称"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">角色</label><input id="profModalRole" type="text" disabled style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;background:#f9f9f9"></div>
<button onclick="saveProfileModal()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;margin-top:4px">保存</button>
<p id="profModalSaveMsg" style="font-size:13px;margin-top:8px;display:none"></p>
<hr style="margin:16px 0;border:none;border-top:1px solid #eee">
<h4 style="margin:0 0 12px 0;font-size:14px;color:#333">修改密码</h4>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">旧密码</label><input id="profModalOldPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="输入当前密码"></div>
<div class="input-group" style="margin-bottom:12px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">新密码</label><input id="profModalNewPwd" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="至少4个字符"></div>
<div class="input-group" style="margin-bottom:16px"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px">确认新密码</label><input id="profModalNewPwd2" type="password" style="width:100%;padding:10px 12px;border:2px solid #eee;border-radius:8px;font-size:14px;outline:none" placeholder="再次输入新密码"></div>
<button onclick="submitProfilePwdModal()" style="padding:10px 24px;background:#667eea;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px">修改密码</button>
<p id="profModalPwdMsg" style="font-size:13px;margin-top:8px;display:none"></p>
</div>
</div>

"""

# Insert profile modal before the password modal
adm = adm.replace(pwd_modal, profile_modal + pwd_modal)
print("2h. Profile modal inserted")

# 2i. Add JS functions for profile modal
last_script = adm.rfind('<script>')
new_js = r"""
<script>
var pwdModalTargetUid = null;
function openPwdModal(uid){ var uname=''; var tbl=document.getElementById('userTableBody'); if(tbl){ var btns=tbl.querySelectorAll('[data-uid]'); for(var b=0;b<btns.length;b++){ if(btns[b].getAttribute('data-uid')==''+uid){ uname=btns[b].getAttribute('data-uname')||''; break; } } } pwdModalTargetUid=uid; document.getElementById('pwdModalTitle').textContent='\u4fee\u6539\u5bc6\u7801 - '+(uname||'#'+uid); document.getElementById('pwdNewInput').value=''; document.getElementById('pwdConfirmInput').value=''; document.getElementById('pwdModalMsg').style.display='none'; document.getElementById('pwdModal').style.display='flex'; }
function closePwdModal(){ document.getElementById('pwdModal').style.display='none'; pwdModalTargetUid=null; }
function submitPwdModal(){ var np=document.getElementById('pwdNewInput').value; var cp=document.getElementById('pwdConfirmInput').value; var msg=document.getElementById('pwdModalMsg'); if(np.length<4){ msg.textContent='\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26'; msg.style.display='block'; return; } if(np!==cp){ msg.textContent='\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4'; msg.style.display='block'; return; } document.getElementById('pwdModalBtn').disabled=true; document.getElementById('pwdModalBtn').textContent='\u63d0\u4ea4\u4e2d...'; fetch('/admin/user/'+pwdModalTargetUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np})}).then(function(r){return r.json();}).then(function(d){if(d.ok){alert('\u5bc6\u7801\u5df2\u4fee\u6539');closePwdModal();}else{msg.textContent=d.detail||'\u4fee\u6539\u5931\u8d25';msg.style.display='block';}}).catch(function(){msg.textContent='\u8bf7\u6c42\u5931\u8d25';msg.style.display='block';}).finally(function(){document.getElementById('pwdModalBtn').disabled=false;document.getElementById('pwdModalBtn').textContent='\u786e\u8ba4\u4fee\u6539';}); }
function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='\u5df2\u4fdd\u5b58';msg.style.color='#27ae60';document.querySelector('[class*=\"user-area\"]').textContent='\ud83d\udc64 '+(dn||'');}else{msg.textContent=d.detail||'\u4fdd\u5b58\u5931\u8d25';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='\u8bf7\u6c42\u5931\u8d25';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='\u8bf7\u8f93\u5165\u65e7\u5bc6\u7801';msg.style.display='block';return;} if(newP.length<4){msg.textContent='\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='\u4e24\u6b21\u8f93\u5165\u7684\u5bc6\u7801\u4e0d\u4e00\u81f4';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='\u5bc6\u7801\u5df2\u4fee\u6539';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'\u4fee\u6539\u5931\u8d25';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='\u8bf7\u6c42\u5931\u8d25';msg.style.color='#e74c3c';msg.style.display='block';}); }
</script>
"""
adm = adm[:last_script] + new_js + adm[last_script:]
print("2i. JS functions added")

# ===== 3. Apply route patches and rebuild =====
result = text[:adm_start_content] + adm + text[adm_end:]

for offset, code in reversed(patches):
    result = result[:offset] + code + result[offset:]
    print(f"  Route patch applied at offset {offset}")

print(f"\nOriginal size: {len(raw)}")
print(f"New size: {len(result.encode('utf-8'))}")

checks = {
    'change_my_password': 'route',
    'admin_change_user_password': 'route',
    'update_me': 'route',
    'openPwdModal(': 'JS',
    'openProfile': 'JS profile',
    'saveProfileModal': 'JS save',
    'profileModal': 'HTML',
    'profModalPwdMsg': 'HTML pwd msg',
}
for key, desc in checks.items():
    count = result.count(key)
    status = 'OK' if count >= 1 else 'MISSING'
    print(f"  [{status}] {key} ({desc}) x{count}")

# Check page-profile is GONE
if 'page-profile' in result:
    print("  [WARN] page-profile still present!")
else:
    print("  [OK] page-profile removed")

import py_compile, tempfile, os
try:
    tmp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
    tmp.write(result.encode('utf-8'))
    tmp.close()
    py_compile.compile(tmp.name, doraise=True)
    os.unlink(tmp.name)
    print(f"\nPython syntax: OK!")
except Exception as e:
    print(f"\nPython syntax error: {e}")

final = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py'
with open(final, 'w', encoding='utf-8') as f:
    f.write(result)
print(f"\nSaved to {final}")
