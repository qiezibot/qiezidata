import re

# ============================================================
# JS payload: complete password change UI
# Written to separate file. Referenced by main file as byte literal.
# ============================================================
js = r"""(function(){
if(document.getElementById('profileModal'))return
var A=document.createElement.bind(document),q=function(id){return document.getElementById(id)},b=document.body
b.insertAdjacentHTML('beforeend','<style>.m{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:1000}.mc{background:#fff;padding:24px;border-radius:12px;width:420px;max-width:90vw;position:relative}.mc span{position:absolute;top:12px;right:16px;font-size:22px;cursor:pointer;color:#999}.fg{margin-bottom:12px}.fg label{display:block;font-size:13px;color:#666;margin-bottom:4px}.fg input{width:100%;padding:8px 10px;border:1px solid #ddd;border-radius:6px;font-size:14px}.mc .btn{width:100%;padding:10px;background:#667eea;color:#fff;border:none;border-radius:8px;font-size:15px;cursor:pointer}.msg{margin-top:10px;padding:10px;border-radius:6px;text-align:center}')
b.insertAdjacentHTML('beforeend','<div id=profileModal class=m><div class=mc><span onclick="pC()">\u00d7</span><h3>\u4e2a\u4eba\u8d44\u6599</h3><div class=fg><label>\u7528\u6237\u540d</label><input id=pU disabled></div><div class=fg><label>\u663e\u793a\u540d\u79f0</label><input id=pDN placeholder=\u8f93\u5165\u663e\u793a\u540d\u79f0></div><div class=fg><label>\u89d2\u8272</label><input id=pR disabled></div><button class=btn onclick=pS()>\u4fdd\u5b58</button><div id=pSM class=msg></div><hr style=margin:16px 0><h4>\u4fee\u6539\u5bc6\u7801</h4><div class=fg><label>\u65e7\u5bc6\u7801</label><input id=pOP type=password placeholder=\u8f93\u5165\u65e7\u5bc6\u7801></div><div class=fg><label>\u65b0\u5bc6\u7801</label><input id=pNP type=password placeholder=\u81f3\u5c114\u4e2a\u5b57\u7b26></div><div class=fg><label>\u786e\u8ba4\u65b0\u5bc6\u7801</label><input id=pNP2 type=password placeholder=\u518d\u6b21\u8f93\u5165></div><button class=btn onclick=pW()>\u4fee\u6539\u5bc6\u7801</button><div id=pWM class=msg></div></div></div><div id=cpModal class=m><div class=mc><span onclick="document.getElementById(\'cpModal\').style.display=\'none\'">\u00d7</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p style=color:#666;font-size:13px>ID: <span id=cpU></span></p><div class=fg><label>\u65b0\u5bc6\u7801</label><input id=cpNP type=password></div><button class=btn onclick=cpW()>\u786e\u8ba4</button><div id=cpM class=msg></div></div></div>')
function pC(){profileModal.style.display='none'}
function pO(){profileModal.style.display='flex';fetch('/me',{credentials:'include'}).then(function(r){return r.json()}).then(function(u){pU.value=u.username||'';pDN.value=u.display_name||'';pR.value=u.role||''})}
function pS(){var dn=pDN.value.trim(),m=pSM;m.style.display='none';fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5df2\u4fdd\u5b58',m.style.color='#27ae60'):(m.textContent=d.detail||'\u4fdd\u5b58\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block';setTimeout(function(){m.style.display='none'},3000)})}
function pW(){var o=pOP.value,n=pNP.value,n2=pNP2.value,m=pWM;m.style.display='none';if(!o){m.textContent='\u8bf7\u8f93\u5165\u65e7\u5bc6\u7801';m.style.display='block';return}if(n.length<4){m.textContent='\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}if(n!=n2){m.textContent='\u4e24\u6b21\u8f93\u5165\u4e0d\u4e00\u81f4';m.style.display='block';return}fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:o,new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5bc6\u7801\u5df2\u4fee\u6539',m.style.color='#27ae60',pOP.value='',pNP.value='',pNP2.value=''):(m.textContent=d.detail||'\u4fee\u6539\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block';setTimeout(function(){m.style.display='none'},3000)})}
var _cu=0
function aCP(u){_cu=u;cpModal.style.display='flex';cpU.textContent=u;cpNP.value='';cpM.style.display='none'}
function cpW(){var n=cpNP.value,m=cpM;m.style.display='none';if(n.length<4){m.textContent='\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.display='block';return}fetch('/admin/user/'+_cu+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5df2\u4fee\u6539',m.style.color='#27ae60',setTimeout(function(){cpModal.style.display='none'},1200)):(m.textContent=d.detail||'\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block'})}
})()

"""

# Save JS for reference
with open('pwd_ui.js', 'w', encoding='utf-8') as f:
    f.write(js)

print(f'JS payload: {len(js)} bytes')
print(f'JS encoded: {len(js.encode("utf-8"))} bytes')

# ============================================================
# Modify railway_file_server.py
# ============================================================
with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 1. Add <script src="/api/pwd-ui.js"> to _ADMIN template
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]
html = html.replace('</body>', '<script src=/api/pwd-ui.js></script>\n</body>')
c = c[:start] + html + c[end:]

# 2. Add /api/pwd-ui.js route 
# The JS payload encoded as a bytes literal to avoid any quoting issues
# Using bytes object with latin-1 encoding (safe for encoded JS)
js_bytes = js.encode('utf-8')
# Represent as integer list to save space  
js_ints = list(js_bytes)

import base64
b64_js = base64.b64encode(js_bytes).decode('ascii')

route_code = f'''

@app.get('/api/pwd-ui.js')
async def pwd_ui(request: Request):
    import base64
    raw = base64.b64decode('{b64_js}')
    return PlainTextResponse(raw, media_type='application/javascript')
'''

name_pos = c.rfind('\nif __name__')
if name_pos < 0:
    name_pos = c.find('if __name__')
c = c[:name_pos] + route_code + c[name_pos:]

# 3. Also modify the user table JS render: add 改密 button
# Find loadUsers render
m2 = re.search(r'_ADMIN\s*=\s*"""', c)
start2 = m2.end()
end_m2 = re.search(r'\n"""', c[start2:])
end2 = start2 + end_m2.start()
html2 = c[start2:end2]

# Add "密码" header column
html2 = html2.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')

# Add button to user rows (both loadUsers and deleteUser renders)
old_end1 = ")+'</td></tr>'}</style>"
# Actually the render ends differently. Let's find the exact pattern.
# It ends with: )+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h
old1 = ")+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new1 = ")+'</td>'+'<td><a id=\\'a'+u.id+'\\' href=# onclick=event.preventDefault();aCP('+u.id+') style=color:#667eea>\\u6539\\u5bc6</a></td></tr>'}document.getElementById('userTableBody').innerHTML=h"

# Actually this approach with escaped quotes is fragile. Let's use a simpler approach.
# Just find and replace the exact ending.
# The loadUsers render: )+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h
old1 = ")+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new1 = ")+'</td>'+'<td><a href=# onclick=\\'event.preventDefault();aCP('+u.id+')\\'>\\u6539\\u5bc6</a></td>'}document.getElementById('userTableBody').innerHTML=h"

# Hmm this is getting complicated with escaped quotes inside triple-quoted strings.
# Let me read the actual template to get the exact text.

print(f'File size: {len(c)} bytes')
print('Will write final...')

import ast
# Check syntax of current c before final write
# The route_code has escaped quotes, need to verify
try:
    ast.parse(c)
    print('Syntax OK!')
except SyntaxError as e:
    print(f'Syntax error: {e}')
