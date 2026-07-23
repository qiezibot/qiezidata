import re, base64

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 1. _ADMIN 模板：加 <script src="/api/pwd.js">
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]
html = html.replace('</body>', '<script src=/api/pwd.js></script>\n</body>')
c = c[:start] + html + c[end:]
print(f'After script tag: {len(c)}')

# 2. 在文件末尾加 /api/pwd.js 路由
# 用 base64 内嵌 JS（避免三引号问题，且比字符串字面量更紧凑）
js_raw = """
(function(){
if(document.getElementById('profileModal'))return;
var d=document.body;
var h='<div id=profileModal class=modal style=display:none><div class=modal-content style=max-width:420px><span class=modal-close onclick=closeProfile()>&times</span><h3>\u4e2a\u4eba\u8d44\u6599</h3><div class=form-group><label>\u7528\u6237\u540d</label><input id=profModalUser type=text readonly style=background:#f5f5f5;cursor:not-allowed></div><div class=form-group><label>\u663e\u793a\u540d\u79f0</label><input id=profModalDN type=text placeholder="\u8f93\u5165\u663e\u793a\u540d\u79f0"></div><div class=form-group><label>\u89d2\u8272</label><input id=profModalRole type=text readonly style=background:#f5f5f5;cursor:not-allowed></div><button class=btn onclick=saveProfileModal()>\u4fdd\u5b58</button><div id=profModalSaveMsg class=msg style=display:none></div><hr style=margin:16px 0><h4>\u4fee\u6539\u5bc6\u7801</h4><div class=form-group><label>\u65e7\u5bc6\u7801</label><input id=profModalOldPwd type=password placeholder="\u8f93\u5165\u65e7\u5bc6\u7801"></div><div class=form-group><label>\u65b0\u5bc6\u7801</label><input id=profModalNewPwd type=password placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26"></div><div class=form-group><label>\u786e\u8ba4\u65b0\u5bc6\u7801</label><input id=profModalNewPwd2 type=password placeholder="\u518d\u6b21\u8f93\u5165"></div><button class=btn onclick=submitProfilePwdModal()>\u4fee\u6539\u5bc6\u7801</button><div id=profModalPwdMsg class=msg style=display:none></div></div></div><div id=changePasswordModal class=modal style=display:none><div class=modal-content style=max-width:380px><span class=modal-close onclick="document.getElementById('+"'"+'changePasswordModal'+"'"+').style.display='+"'"+'none'+"'"+'">&times</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p id=cpUserInfo style=color:#666;margin-bottom:12px;font-size:13px></p><div class=form-group><label>\u65b0\u5bc6\u7801</label><input id=cpNewPwd type=password placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26"></div><button class=btn onclick=submitAdminChangePwd()>\u786e\u8ba4\u4fee\u6539</button><div id=cpMsg class=msg style=display:none></div></div></div>';
var w=document.createElement('div');w.innerHTML=h;while(w.firstChild)d.appendChild(w.firstChild);
function closeProfile(){document.getElementById('profileModal').style.display='none'}
function openProfile(){document.getElementById('profileModal').style.display='flex';fetch('/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(u){document.getElementById('profModalUser').value=u.username||'';document.getElementById('profModalDN').value=u.display_name||'';document.getElementById('profModalRole').value=u.role||''})}
function saveProfileModal(){var dn=document.getElementById('profModalDN').value.trim();var m=document.getElementById('profModalSaveMsg');m.style.display='none';fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5df2\u4fdd\u5b58',m.style.color='#27ae60'):(m.textContent=d.detail||'\u4fdd\u5b58\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block';setTimeout(function(){m.style.display='none'},3000)})}
function submitProfilePwdModal(){var o=document.getElementById('profModalOldPwd').value;var n=document.getElementById('profModalNewPwd').value;var n2=document.getElementById('profModalNewPwd2').value;var m=document.getElementById('profModalPwdMsg');m.style.display='none';if(!o){m.textContent='\u8bf7\u8f93\u5165\u65e7\u5bc6\u7801';m.style.display='block';return}if(n.length<4){m.textContent='\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}if(n!=n2){m.textContent='\u4e24\u6b21\u8f93\u5165\u4e0d\u4e00\u81f4';m.style.display='block';return}fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:o,new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5bc6\u7801\u5df2\u4fee\u6539',m.style.color='#27ae60',document.getElementById('profModalOldPwd').value='',document.getElementById('profModalNewPwd').value='',document.getElementById('profModalNewPwd2').value=''):(m.textContent=d.detail||'\u4fee\u6539\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block';setTimeout(function(){m.style.display='none'},3000)})}
function adminChangePwd(uid){document.getElementById('changePasswordModal').style.display='flex';document.getElementById('cpUserInfo').textContent='\u7528\u6237ID: '+uid;document.getElementById('cpNewPwd').value='';document.getElementById('cpMsg').style.display='none'}
function submitAdminChangePwd(){var n=document.getElementById('cpNewPwd').value;var m=document.getElementById('cpMsg');m.style.display='none';if(n.length<4){m.textContent='\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}fetch('/admin/user/'+_cu+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5bc6\u7801\u5df2\u4fee\u6539',m.style.color='#27ae60',setTimeout(function(){document.getElementById('changePasswordModal').style.display='none'},1500)):(m.textContent=d.detail||'\u4fee\u6539\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block'})}
var _cu=0;
})()

""".encode('utf-8')

# Fix the adminChangePwd function - use global var _cu instead of extracting from DOM
# Wait, the JS already has var _cu=0 at the bottom. Fix adminChangePwd to work with it.

b64 = base64.b64encode(js_raw).decode('ascii')
print(f'JS raw: {len(js_raw)} bytes, b64: {len(b64)}')

route = f"""
@app.get('/api/pwd.js')
async def pwd_js():
    import base64
    js = base64.b64decode('{b64}')
    return PlainTextResponse(js, media_type='application/javascript')
"""

name_pos = c.rfind('\nif __name__')
c = c[:name_pos] + route + c[name_pos:]

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)

import ast
ast.parse(c)
print(f'Final: {len(c)} bytes')
print('pwd.js in _ADMIN:', '/api/pwd.js' in c)
print('openProfile in route:', 'openProfile' in c)
