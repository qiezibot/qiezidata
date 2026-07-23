import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# ===== 1. 路由 =====
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
        if not row or row['password_hash'] != _hash(old_pw):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=?', uid)
        if not row or row['password_hash'] != _hash(old_pw):
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
if m:
    pos = idx + m.start() + 1
    c = c[:pos] + routes + c[pos:]
    print('+ 3 routes added')
else:
    print('ERROR: no @app found after /me')
    exit(1)

# ===== 2. _ADMIN 模板 =====
# 找 _ADMIN 起止
m = re.search(r'_ADMIN\s*=\s*"""', c)
if not m: print('ERROR: _ADMIN not found'); exit(1)
start = m.end()
end = c.find('\n"""', start)
html = c[start:end]

# 2a. 侧边栏加个人资料入口（在用户管理前）
html = html.replace(
    'data-page="page-users"',
    'data-page="page-profile" onclick="openProfile()"><span class="nav-icon">👤</span><span class="nav-text">个人资料</span></li><li class="nav-item" data-page="page-users"'
)
print('+ sidebar nav item')

# 2b. 用户表头加密码列
html = html.replace('</thead>', '<th style="width:100px">密码</th></thead>')
print('+ th column')

# 2c. 每行加密码按钮（在删除按钮前）
html = html.replace(
    'onclick="deleteUser(',
    '<button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})" style="margin-right:4px">修改密码</button> <button onclick="deleteUser('
)
print('+ per-row button')

# 2d. </body> 前加模态框
modal_html = '''
<!-- 个人资料弹窗 -->
<div id="profileModal" class="modal" style="display:none"><div class="modal-content" style="max-width:420px"><span class="modal-close" onclick="closeProfile()">&times;</span><h3>个人资料</h3><div class="form-group"><label>用户名</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><div class="form-group"><label>显示名称</label><input id="profModalDN" type="text" placeholder="输入显示名称"></div><div class="form-group"><label>角色</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><button class="btn" onclick="saveProfileModal()">保存</button><div id="profModalSaveMsg" class="msg" style="display:none"></div><hr style="margin:16px 0"><h4>修改密码</h4><div class="form-group"><label>旧密码</label><input id="profModalOldPwd" type="password" placeholder="输入旧密码"></div><div class="form-group"><label>新密码</label><input id="profModalNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认新密码</label><input id="profModalNewPwd2" type="password" placeholder="再次输入"></div><button class="btn" onclick="submitProfilePwdModal()">修改密码</button><div id="profModalPwdMsg" class="msg" style="display:none"></div></div></div>
<!-- 管理员改用户密码 -->
<div id="changePasswordModal" class="modal" style="display:none"><div class="modal-content" style="max-width:380px"><span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span><h3>修改用户密码</h3><p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p><div class="form-group"><label>新密码</label><input id="cpNewPwd" type="password" placeholder="至少4个字符"></div><button class="btn" onclick="submitAdminChangePwd()">确认修改</button><div id="cpMsg" class="msg" style="display:none"></div></div></div>
'''
html = html.replace('</body>', modal_html + '\n</body>')
print('+ modals')

# 2e. </script> 前加JS函数
js = """
function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;} if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='两次输入不一致';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
var _cpUid=0;
function adminChangePwd(uid){ _cpUid=uid; document.getElementById('changePasswordModal').style.display='flex'; document.getElementById('cpUserInfo').textContent='用户ID: '+uid; document.getElementById('cpNewPwd').value=''; document.getElementById('cpMsg').style.display='none'; }
function submitAdminChangePwd(){ var newP=document.getElementById('cpNewPwd').value; var msg=document.getElementById('cpMsg'); msg.style.display='none'; if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
"""
html = html.replace('</script>', '</script>\n' + js)
print('+ JS functions')

c = c[:start] + html + c[end:]
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print(f'Done! File: {len(c)} bytes')
