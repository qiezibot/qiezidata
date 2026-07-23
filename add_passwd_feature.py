import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 新的后端路由
new_routes = r'''

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
    aid = _require(request); user = await _user(aid)
    if not user or user.get('role') != 'admin': raise HTTPException(status_code=403)
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
'''

# 在 get_me 后面插入
idx = c.rfind("@app.get('/me')")
if idx < 0:
    idx = c.rfind('@app.get("/me")')
print(f'Found GET /me at {idx}')

# 找到 get_me 函数结束（下一个 @app.）
after = c[idx + len("@app.get('/me')"):]
next_route = re.search(r'\n@app\.', after)
if next_route:
    insert_pos = idx + len("@app.get('/me')") + next_route.start() + 1
    c = c[:insert_pos] + new_routes + c[insert_pos:]
    print(f'Inserted routes at position {insert_pos}')
else:
    print('Could not find next route')
    # 备选：在文件末尾加
    c = c + new_routes

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print('Backend routes: Syntax OK')

# ===== 2. 修改 _ADMIN 模板加前端UI =====
# 重新读取
with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

_ADMIN_START = '_ADMIN = """'
_ADMIN_END = '"""'

# 找 _ADMIN 的开始和结束
admin_start = c.find(_ADMIN_START)
admin_end = c.rfind(_ADMIN_END)
if admin_start < 0 or admin_end < 0:
    print('_ADMIN not found')
    exit(1)

admin_start += len(_ADMIN_START)
admin_html = c[admin_start:admin_end]
print(f'_ADMIN HTML: {len(admin_html)} bytes')

# (a) 在侧边栏加"个人资料"入口
# 找到侧边栏的 user area
sidebar_item = '<li class="nav-item" data-page="page-users"'
if sidebar_item in admin_html:
    # 在 user 管理前面加个人资料
    profile_nav = '''<li class="nav-item" data-page="page-profile" onclick="openProfile()"><span class="nav-icon">👤</span><span class="nav-text">个人资料</span></li>\n                    '''
    admin_html = admin_html.replace(sidebar_item, profile_nav + '                    ' + sidebar_item)
    print('Added profile nav item')
else:
    print('Could not find sidebar users item')

# (b) 在用户管理表头加"修改密码"列
# 找到用户表的表头
th_matches = list(re.finditer(r'<th[^>]*>.*?</th>', admin_html, re.IGNORECASE))
for m in th_matches:
    pass  # 先看看表头结构
# 简单方法：在最后一个 th 前插入
last_th = admin_html.rfind('</th>', 0, admin_html.find('</thead>') if '</thead>' in admin_html else len(admin_html))
if last_th > 0:
    # 在最后一个 th 前插入密码列
    insert_at = last_th
    pwd_th = '<th style="width:100px">密码</th>'
    admin_html = admin_html[:insert_at] + pwd_th + admin_html[insert_at:]
    print('Added password th')
else:
    print('Could not find last th')

# (c) 在用户表每行加"修改密码"按钮
# 找到用户行的操作列（通常在最后一个 td）
td_pattern = re.compile(r'(<td[^>]*>.*?</td>\s*)+</tr>', re.DOTALL)
# 简单方法：在每个 tr 的最后一个 td 前加上密码按钮
admin_html = admin_html.replace(
    '${user.display_name||user.username}</td>',
    '${user.display_name||user.username}</td><td><button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})">修改密码</button></td>'
)
if '${user.display_name' in admin_html:
    print('Added password button to user rows')
else:
    print('Could not find display_name cell, trying alternative...')
    # 备选：在删除按钮附近加
    admin_html = admin_html.replace(
        'onclick="deleteUser(',
        '<button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})">修改密码</button> <button class="btn-small btn-danger" onclick="deleteUser('
    )
    print('Added near delete button')

# (d) 添加模态框和JS函数
# 在 </body> 前插入 profileModal 和 changePasswordModal
modal_html = '''
<!-- 个人资料弹窗 -->
<div id="profileModal" class="modal" style="display:none">
  <div class="modal-content" style="max-width:420px">
    <span class="modal-close" onclick="closeProfile()">&times;</span>
    <h3>个人资料</h3>
    <div class="form-group">
      <label>用户名</label>
      <input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed">
    </div>
    <div class="form-group">
      <label>显示名称</label>
      <input id="profModalDN" type="text" placeholder="输入显示名称">
    </div>
    <div class="form-group">
      <label>角色</label>
      <input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed">
    </div>
    <button class="btn" onclick="saveProfileModal()">保存</button>
    <div id="profModalSaveMsg" class="msg" style="display:none"></div>
    <hr style="margin:16px 0">
    <h4>修改密码</h4>
    <div class="form-group">
      <label>旧密码</label>
      <input id="profModalOldPwd" type="password" placeholder="输入旧密码">
    </div>
    <div class="form-group">
      <label>新密码</label>
      <input id="profModalNewPwd" type="password" placeholder="至少4个字符">
    </div>
    <div class="form-group">
      <label>确认新密码</label>
      <input id="profModalNewPwd2" type="password" placeholder="再次输入新密码">
    </div>
    <button class="btn" onclick="submitProfilePwdModal()">修改密码</button>
    <div id="profModalPwdMsg" class="msg" style="display:none"></div>
  </div>
</div>

<!-- 管理员修改用户密码弹窗 -->
<div id="changePasswordModal" class="modal" style="display:none">
  <div class="modal-content" style="max-width:380px">
    <span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span>
    <h3>修改用户密码</h3>
    <p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p>
    <div class="form-group">
      <label>新密码</label>
      <input id="cpNewPwd" type="password" placeholder="至少4个字符">
    </div>
    <button class="btn" onclick="submitAdminChangePwd()">确认修改</button>
    <div id="cpMsg" class="msg" style="display:none"></div>
  </div>
</div>
'''

# 在 </body> 前插入
admin_html = admin_html.replace('</body>', modal_html + '\n</body>')
print('Added modals')

# 同时插入 JS 函数（在最后一个 </script> 前）
js_functions = '''
function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;} if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='两次输入的密码不一致';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
var _cpUid=0;
function adminChangePwd(uid){ _cpUid=uid; document.getElementById('changePasswordModal').style.display='flex'; document.getElementById('cpUserInfo').textContent='用户ID: '+uid; document.getElementById('cpNewPwd').value=''; document.getElementById('cpMsg').style.display='none'; }
function submitAdminChangePwd(){ var newP=document.getElementById('cpNewPwd').value; var msg=document.getElementById('cpMsg'); msg.style.display='none'; if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
'''

last_script = admin_html.rfind('</script>')
if last_script > 0:
    admin_html = admin_html[:last_script] + js_functions + '\n' + admin_html[last_script:]
    print('Added JS functions')
else:
    print('Could not find last script')

# 写回
c = c[:admin_start] + admin_html + c[admin_end:]
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print('Final: Syntax OK')
print(f'File size: {len(c)} bytes')
