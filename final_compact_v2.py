import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# _ADMIN 确切范围
ADMIN_START = 38238  # skip triple-quote
ADMIN_END = 68089    # position of closing """

# Step 1: compress empty lines in entire file
lines = c.split('\n')
result = []
empty_run = 0
for line in lines:
    if not line.strip():
        empty_run += 1
        if empty_run <= 2:
            result.append('')
    else:
        empty_run = 0
        result.append(line)
c = '\n'.join(result)
print(f'After compression: {len(c)} bytes')

# Recalculate _ADMIN position after compression
# Read file again with new c
html_start = c.find(r'_ADMIN = """\<!')
if html_start < 0:
    html_start = c.find(r'_ADMIN = """\\')
assert html_start >= 0
# After the opening """
open_quote = html_start + len('_ADMIN = """')
# Find closing """  
# The closing is """ followed by newline (not part of other strings)
# Search from open_quote for the first \n""" that ends html
# The html ends with </html>
close_marker = 'html>"""'
close_pos = c.find(close_marker, open_quote)
assert close_pos >= 0
# The """ after the html
ADMIN_END_NEW = close_pos + len(close_marker)
ADMIN_START_NEW = open_quote + 1  # after the \ that escapes

print(f'new ADMIN: {ADMIN_START_NEW}-{ADMIN_END_NEW}')
html = c[ADMIN_START_NEW:ADMIN_END_NEW]
print(f'ADMIN size: {len(html)}')

# Step 2: Add "密码" header after "操作"
html = html.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')
print('Added header column')

# Step 3: Add "改密" button in user rows
# Two places: loadUsers() and deleteUser()
# Both have: h+='<tr><td>'... same pattern
# Find the exact render string
render_start = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'"
# This appears twice. After each </td></tr>' at the end, we add another cell

# Strategy: replace the </td></tr>' at the end of loadUsers render
# Find `'</td></tr>'` that's followed by `}document.getElementById`
old_suffix1 = "'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new_suffix1 = "'+'</td><td>'+('<a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=\"color:#667eea;font-size:13px\">\u6539\u5bc6</a>'):'-')+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"

# And the same for deleteUser
old_suffix2 = "'</td></tr>'}document.getElementById('myFileList').innerHTML=h"
new_suffix2 = "'+'</td><td>'+('<a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=\"color:#667eea;font-size:13px\">\u6539\u5bc6</a>'):'-')+'</td></tr>'}document.getElementById('myFileList').innerHTML=h"

old_suffix3 = "'</td></tr>'}document.getElementById('fileTableBody').innerHTML=h"
new_suffix3 = "'+'</td><td>'+('<a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=\"color:#667eea;font-size:13px\">\u6539\u5bc6</a>'):'-')+'</td></tr>'}document.getElementById('fileTableBody').innerHTML=h"

# Actually this is too fragile. Simpler: find the loadUsers render that has role==='admin' check
# The pattern is: )+'</td></tr>'}
# After the delete button block
old = ")+'</td></tr>'}document.getElementById('userTableBody')"
new = ")+'</td>'+'<td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('userTableBody')"
html = html.replace(old, new)

# Same for deleteUser render
old2 = ")+'</td></tr>'}document.getElementById('fileTableBody')"
if old2 in html:
    new2 = ")+'</td>'+'<td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('fileTableBody')"
    html = html.replace(old2, new2)
else:
    # Try the other one
    # In deleteUser the render is: '<td>'+(u.role...)+'</td></tr>'}document.getElementById('myFileList')
    old2b = ")+'</td></tr>'}document.getElementById('myFileList')"
    if old2b in html:
        new2b = ")+'</td>'+'<td><a href=# onclick=\"event.preventDefault();pwdm('+u.id+')\" style=color:#667eea;font-size:13px>\u6539\u5bc6</a></td></tr>'}document.getElementById('myFileList')"
        html = html.replace(old2b, new2b)

print('Added render cells')

# Step 4: Add modal + script before </body>
modal = '<div id=pwdm class=modal style=display:none><div class=modal-content style=max-width:360px><span class=modal-close onclick="pm()">&times;</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p style=color:#666;margin-bottom:12px;font-size:13px>\u7528\u6237ID: <span id=puid></span></p><div class=form-group><label>\u65b0\u5bc6\u7801</label><input id=pnp type=password></div><button class=btn onclick=pwok()>\u786e\u8ba4</button><div id=pwmsg style=display:none></div></div></div><script>function pm(){document.getElementById("pwdm").style.display="none"}function pwdm(uid){document.getElementById("puid").textContent=uid;document.getElementById("pnp").value="";document.getElementById("pwmsg").style.display="none";document.getElementById("pwdm").style.display="flex"}function pwok(){var np=document.getElementById("pnp").value;var m=document.getElementById("pwmsg");m.style.display="none";if(np.length<4){m.textContent="\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26";m.style.color="#e74c3c";m.style.display="block";return}var uid=parseInt(document.getElementById("puid").textContent);fetch("/admin/user/"+uid+"/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_password:np})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="\u5df2\u4fee\u6539",m.style.color="#27ae60",setTimeout(function(){document.getElementById("pwdm").style.display="none"},1200)):(m.textContent=d.detail||"\u5931\u8d25",m.style.color="#e74c3c");m.style.display="block"})}</script>'
html = html.replace('</body>', modal + '\n</body>')
print('Added modal')

# Rebuild
c = c[:ADMIN_START_NEW] + html + c[ADMIN_END_NEW:]

# Verify syntax
import ast
ast.parse(c)
print(f'FINAL: {len(c)} bytes')
print(f'Over limit: {len(c) - 86000} bytes')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
