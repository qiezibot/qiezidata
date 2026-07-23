import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 找 _ADMIN
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end = c.find('\n"""', start)
html = c[start:end]

# 1. 侧边栏加个人资料
html = html.replace(
    'data-page="page-users"',
    'data-page="page-profile" onclick="openProfile()"><span class="nav-icon">\U0001f464</span><span class="nav-text">个人资料</span></li><li class="nav-item" data-page="page-users"'
)
# 2. 用户表格加密码列
html = html.replace('</thead>', '<th style="width:100px">密码</th></thead>')
# 3. 每行加密码按钮
html = html.replace(
    'onclick="deleteUser(',
    '<button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})" style="margin-right:4px">修改密码</button> <button onclick="deleteUser('
)
# 4. 用户名可点击
html = html.replace(
    '"><span class="user-area">\U0001f464; <!--U--></span>',
    '"><span class="user-area"><a onclick="openProfile()" style="cursor:pointer;color:inherit;text-decoration:none">\U0001f464; <!--U--></a></span>'
)
# 5. body前加模态框 + JS（一行，极致压缩）
modal_js = """\n<div id="profileModal" class="modal" style="display:none"><div class="modal-content" style="max-width:420px"><span class="modal-close" onclick="closeProfile()">&times;</span><h3>个人资料</h3><div class="form-group"><label>用户名</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><div class="form-group"><label>显示名称</label><input id="profModalDN" type="text" placeholder="输入显示名称"></div><div class="form-group"><label>角色</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><button class="btn" onclick="saveProfileModal()">保存</button><div id="profModalSaveMsg" class="msg" style="display:none"></div><hr style="margin:16px 0"><h4>修改密码</h4><div class="form-group"><label>旧密码</label><input id="profModalOldPwd" type="password" placeholder="输入旧密码"></div><div class="form-group"><label>新密码</label><input id="profModalNewPwd" type="password" placeholder="至少4个字符"></div><div class="form-group"><label>确认新密码</label><input id="profModalNewPwd2" type="password" placeholder="再次输入"></div><button class="btn" onclick="submitProfilePwdModal()">修改密码</button><div id="profModalPwdMsg" class="msg" style="display:none"></div></div></div>\n<div id="changePasswordModal" class="modal" style="display:none"><div class="modal-content" style="max-width:380px"><span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span><h3>修改用户密码</h3><p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p><div class="form-group"><label>新密码</label><input id="cpNewPwd" type="password" placeholder="至少4个字符"></div><button class="btn" onclick="submitAdminChangePwd()">确认修改</button><div id="cpMsg" class="msg" style="display:none"></div></div></div>\n<script>
function openProfile(){document.getElementById('profileModal').style.display='flex';fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){document.getElementById('profModalUser').value=u.username||'';document.getElementById('profModalDN').value=u.display_name||'';document.getElementById('profModalRole').value=u.role||'';});}
function closeProfile(){document.getElementById('profileModal').style.display='none';}
function saveProfileModal(){var dn=document.getElementById('profModalDN').value.trim();var msg=document.getElementById('profModalSaveMsg');msg.style.display='none';fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';});}
function submitProfilePwdModal(){var oldP=document.getElementById('profModalOldPwd').value;var newP=document.getElementById('profModalNewPwd').value;var newP2=document.getElementById('profModalNewPwd2').value;var msg=document.getElementById('profModalPwdMsg');msg.style.display='none';if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;}if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;}if(newP!==newP2){msg.textContent='两次输入不一致';msg.style.display='block';return;}fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);});}
var _cpUid=0;
function adminChangePwd(uid){_cpUid=uid;document.getElementById('changePasswordModal').style.display='flex';document.getElementById('cpUserInfo').textContent='用户ID: '+uid;document.getElementById('cpNewPwd').value='';document.getElementById('cpMsg').style.display='none';}
function submitAdminChangePwd(){var newP=document.getElementById('cpNewPwd').value;var msg=document.getElementById('cpMsg');msg.style.display='none';if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;}fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';});}
</script>"""
html = html.replace('</body>', modal_js + '\n</body>')

# 压缩多余空行
html = re.sub(r'\n{3,}', '\n\n', html)

c = c[:start] + html + c[end:]
print(f'Before: {len(open("railway_file_server.py", encoding="utf-8").read())} bytes')
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print(f'After: {len(c)} bytes')
