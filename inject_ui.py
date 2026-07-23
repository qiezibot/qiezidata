import sys, re
sys.stdout.reconfigure(encoding='utf-8')

CS = 37522  # _ADMIN content start (after """\)
CE = 67150  # _ADMIN content end (after html>""")

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

html = c[CS:CE]

# 1. Add "密码" column in table header
html = html.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')

# 2. In loadUsers: after the role/admin render + '</td></tr>', insert another cell
# loadUsers has: )+'</td></tr>'}document.getElementById('userTableBody')
# deleteUser has: )+'</td></tr>'}document.getElementById('myFileList')
old_render_end1 = ")+'</td></tr>'}document.getElementById('userTableBody')"
new_render_end1 = ")+'</td><td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('userTableBody')"
if old_render_end1 in html:
    html = html.replace(old_render_end1, new_render_end1)
else:
    # Try with template literal
    old_alt1 = ")+'</td></tr>'}document.getElementById('userTableBody')"
    if old_alt1 not in html:
        # Show nearby content
        test = ")+'</td></tr>'"
        pos = html.find(test)
        print(f'Test pattern at {pos}: {repr(html[pos:pos+80])}')
    else:
        html = html.replace(old_alt1, new_render_end1)

old_render_end2 = ")+'</td></tr>'}document.getElementById('myFileList')"
if old_render_end2 in html:
    new_render_end2 = ")+'</td><td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('myFileList')"
    html = html.replace(old_render_end2, new_render_end2)

# Also check for fileTableBody (admin file list)
old_render_end3 = ")+'</td></tr>'}document.getElementById('fileTableBody')"
if old_render_end3 in html:
    new_render_end3 = ")+'</td><td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('fileTableBody')"
    html = html.replace(old_render_end3, new_render_end3)

# 3. Add modal + script before </body>
modal = ('<div id=pwdm class=modal style=display:none>'
'<div class=modal-content style=max-width:360px>'
'<span class=modal-close onclick=pm()>&times;</span>'
'<h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3>'
'<p style=color:#666;font-size:13px>ID: <span id=puid></span></p>'
'<div class=form-group><label>\u65b0\u5bc6\u7801</label><input id=pnp type=password></div>'
'<button class=btn onclick=pwok()>\u786e\u8ba4</button>'
'<div id=pwmsg></div></div></div>'
'<script>function pm(){pwdm.style.display="none"}'
'function pwdm(uid){puid.textContent=uid;pnp.value="";document.getElementById("pwmsg").style.display="none";document.getElementById("pwdm").style.display="flex"}'
'function pwok(){var np=pnp.value;var m=document.getElementById("pwmsg");m.style.display="none";if(np.length<4){m.textContent="\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26";m.style.color="#e74c3c";m.style.display="block";return}var uid=parseInt(puid.textContent);fetch("/admin/user/"+uid+"/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_password:np})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="\u5df2\u4fee\u6539",m.style.color="#27ae60",setTimeout(function(){document.getElementById("pwdm").style.display="none"},1200)):(m.textContent=d.detail||"\u5931\u8d25",m.style.color="#e74c3c");m.style.display="block"})}'
'</script>')
html = html.replace('</body>', modal + '\n</body>')

c = c[:CS] + html + c[CE:]
print(f'Modal size: {len(modal)}')

import ast
ast.parse(c)
print(f'FINAL: {len(c)} bytes')
print(f'Over 86KB: {len(c) - 86000} bytes')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
