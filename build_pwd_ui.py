"""
Build the final railway_file_server.py by inserting:
  - A <script src='/api/pwd.js'> line into _ADMIN template
  - A /api/pwd.js route that returns all the password UI JS+HTML
Method: read the base file, do precise string operations, write + verify.
"""
import re

BASE = 'railway_file_server.py'

# ---------------------------------------------------------------------------
# 1. Read base file
# ---------------------------------------------------------------------------
with open(BASE, encoding='utf-8') as f:
    src = f.read()

# ---------------------------------------------------------------------------
# 2. Insert <script src='/api/pwd.js'> just before </body> inside _ADMIN
# ---------------------------------------------------------------------------
# Locate _ADMIN = """ ... """
m = re.search(r'_ADMIN\s*=\s*"""', src)
assert m, 'Cannot find _ADMIN'
adm_start = m.end()
adm_end_m = re.search(r'\n"""', src[adm_start:])
adm_end = adm_start + adm_end_m.start()

html = src[adm_start:adm_end]

# Insert the external script line before </body>
html = html.replace('</body>', '<script src="/api/pwd.js"></script>\n</body>')

src = src[:adm_start] + html + src[adm_end:]

# ---------------------------------------------------------------------------
# 3. Append /api/pwd.js route before if __name__
# ---------------------------------------------------------------------------
# The JS + HTML payload is stored as a Python bytes literal (no quoting issues)
# but we can use a simple trick:
#   Write the JS+HTML payload to a separate file at build time (it ships
#   alongside the main .py file on Railway).
# However, we only push one file. So we'll embed it as a very carefully
# constructed f-string where the payload is base64.b64decode'd at runtime.
# 
# Simpler: Write the route with the payload as a raw triple-quoted string
# but keep the payload SHORT. Since the JS+HTML is ~7KB, use base64.
import base64

# Build the JS payload as raw bytes
JS_PAYLOAD_BYTES = r"""/* profileModal + changePasswordModal */
(function(){
if(document.getElementById('profileModal'))return;
var d=document.body;

/* --- HTML for both modals --- */
var h='<div id="profileModal" class="modal" style="display:none"><div class="modal-content" style="max-width:420px"><span class="modal-close" onclick="closeProfile()">&times;</span><h3>\u4e2a\u4eba\u8d44\u6599</h3><div class="form-group"><label>\u7528\u6237\u540d</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><div class="form-group"><label>\u663e\u793a\u540d\u79f0</label><input id="profModalDN" type="text" placeholder="\u8f93\u5165\u663e\u793a\u540d\u79f0"></div><div class="form-group"><label>\u89d2\u8272</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div><button class="btn" onclick="saveProfileModal()">\u4fdd\u5b58</button><div id="profModalSaveMsg" class="msg" style="display:none"></div><hr style="margin:16px 0"><h4>\u4fee\u6539\u5bc6\u7801</h4><div class="form-group"><label>\u65e7\u5bc6\u7801</label><input id="profModalOldPwd" type="password" placeholder="\u8f93\u5165\u65e7\u5bc6\u7801"></div><div class="form-group"><label>\u65b0\u5bc6\u7801</label><input id="profModalNewPwd" type="password" placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26"></div><div class="form-group"><label>\u786e\u8ba4\u65b0\u5bc6\u7801</label><input id="profModalNewPwd2" type="password" placeholder="\u518d\u6b21\u8f93\u5165"></div><button class="btn" onclick="submitProfilePwdModal()">\u4fee\u6539\u5bc6\u7801</button><div id="profModalPwdMsg" class="msg" style="display:none"></div></div></div>'
+'<div id="changePasswordModal" class="modal" style="display:none"><div class="modal-content" style="max-width:380px"><span class="modal-close" onclick="document.getElementById("changePasswordModal").style.display="none"">&times;</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p><div class="form-group"><label>\u65b0\u5bc6\u7801</label><input id="cpNewPwd" type="password" placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26"></div><button class="btn" onclick="submitAdminChangePwd()">\u786e\u8ba4\u4fee\u6539</button><div id="cpMsg" class="msg" style="display:none"></div></div></div>';
var w=document.createElement('div');w.innerHTML=h;while(w.firstChild)d.appendChild(w.firstChild);

/* --- JS Functions --- */
function closeProfile(){document.getElementById('profileModal').style.display='none'}
function openProfile(){
  document.getElementById('profileModal').style.display='flex';
  fetch('/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(u){
    document.getElementById('profModalUser').value=u.username||'';
    document.getElementById('profModalDN').value=u.display_name||'';
    document.getElementById('profModalRole').value=u.role||'';
  });
}
function saveProfileModal(){
  var dn=document.getElementById('profModalDN').value.trim();
  var m=document.getElementById('profModalSaveMsg');m.style.display='none';
  fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})})
  .then(function(r){return r.json()}).then(function(d){
    d.ok?(m.textContent='\u5df2\u4fdd\u5b58',m.style.color='#27ae60'):(m.textContent=d.detail||'\u4fdd\u5b58\u5931\u8d25',m.style.color='#e74c3c');
    m.style.display='block';setTimeout(function(){m.style.display='none'},3000);
  });
}
function submitProfilePwdModal(){
  var o=document.getElementById('profModalOldPwd').value;
  var n=document.getElementById('profModalNewPwd').value;
  var n2=document.getElementById('profModalNewPwd2').value;
  var m=document.getElementById('profModalPwdMsg');m.style.display='none';
  if(!o){m.textContent='\u8bf7\u8f93\u5165\u65e7\u5bc6\u7801';m.style.display='block';return}
  if(n.length<4){m.textContent='\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}
  if(n!=n2){m.textContent='\u4e24\u6b21\u8f93\u5165\u4e0d\u4e00\u81f4';m.style.display='block';return}
  fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:o,new_password:n})})
  .then(function(r){return r.json()}).then(function(d){
    d.ok?(m.textContent='\u5bc6\u7801\u5df2\u4fee\u6539',m.style.color='#27ae60',document.getElementById('profModalOldPwd').value='',document.getElementById('profModalNewPwd').value='',document.getElementById('profModalNewPwd2').value=''):(m.textContent=d.detail||'\u4fee\u6539\u5931\u8d25',m.style.color='#e74c3c');
    m.style.display='block';setTimeout(function(){m.style.display='none'},3000);
  });
}
function adminChangePwd(uid){document.getElementById('changePasswordModal').style.display='flex';document.getElementById('cpUserInfo').textContent='\u7528\u6237ID: '+uid;document.getElementById('cpNewPwd').value='';document.getElementById('cpMsg').style.display='none'}
function submitAdminChangePwd(){
  var n=document.getElementById('cpNewPwd').value;
  var m=document.getElementById('cpMsg');m.style.display='none';
  if(n.length<4){m.textContent='\u65b0\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}
  var uid=document.getElementById('cpUserInfo').textContent.split(': ')[1];
  fetch('/admin/user/'+uid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:n})})
  .then(function(r){return r.json()}).then(function(d){
    d.ok?(m.textContent='\u5bc6\u7801\u5df2\u4fee\u6539',m.style.color='#27ae60',setTimeout(function(){document.getElementById('changePasswordModal').style.display='none'},1500)):(m.textContent=d.detail||'\u4fee\u6539\u5931\u8d25',m.style.color='#e74c3c');
    m.style.display='block';
  });
}
})();
""".encode('utf-8')

b64_payload = base64.b64encode(JS_PAYLOAD_BYTES).decode('ascii')

# The route: decode base64 at runtime and serve
route_block = f'''

@app.get('/api/pwd.js')
async def pwd_js():
    import base64
    js = base64.b64decode("{b64_payload}").decode('utf-8')
    return PlainTextResponse(js, media_type='application/javascript')
'''

# Find insertion point
name_pos = src.rfind('\nif __name__')
if name_pos < 0:
    # Search for "if __name__"
    name_pos = src.find("if __name__")

src = src[:name_pos] + route_block + src[name_pos:]

# ---------------------------------------------------------------------------
# 4. Verify syntax
# ---------------------------------------------------------------------------
with open(BASE, 'w', encoding='utf-8') as f:
    f.write(src)

import ast
ast.parse(src)
print(f'OK! {len(src)} bytes')
print('Check: /api/pwd.js in _ADMIN:', '/api/pwd.js' in src)
print('Check: openProfile in route:', 'openProfile' in src)
