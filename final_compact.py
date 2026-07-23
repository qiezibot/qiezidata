"""
Final build: compressed template + minimal password change UI.
Target: < 86KB
"""
import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# Step 1: Compress empty lines (max 2 consecutive)
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

# Step 2: Modify _ADMIN
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 2a: Add "改密" header column after "操作"
html = html.replace(
    '<th>\u64cd\u4f5c</th>',  # <th>操作</th>
    '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>'  # <th>操作</th><th>密码</th>
)

# 2b: In loadUsers() function, add a "改密" button after the admin/set-admin buttons
# Find the line with role==='admin' check
old_render = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style=\"color:green\">\u5df2\u662f\u7ba1\u7406\u5458</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">\u8bbe\u4e3a\u7ba1\u7406\u5458</button>')+'</td></tr>'"

# New render: same but with one more cell for "改密" with onclick
new_render = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style=\"color:green\">\u5df2\u662f\u7ba1\u7406\u5458</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">\u8bbe\u4e3a\u7ba1\u7406\u5458</button>')+'</td><td><a href=\"#\" onclick=\"event.preventDefault();pwdm('+u.id+')\" style=\"color:#667eea\">\u6539\u5bc6</a></td></tr>'"

c = c.replace(old_render, new_render)

# Also fix the duplicate render in deleteUser function
old_render2 = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button>')+'</td></tr>'"
new_render2 = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'-':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button>')+'</td><td><a href=\"#\" onclick=\"event.preventDefault();pwdm('+u.id+')\" style=\"color:#667eea\">\u6539\u5bc6</a></td></tr>'"
c = c.replace(old_render2, new_render2)

# 2c: Add modal HTML + script before </body>
modal = """<div id="pwdm" class="modal" style="display:none"><div class="modal-content" style="max-width:360px"><span class="modal-close" onclick="document.getElementById('pwdm').style.display='none'">&times;</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><p style="color:#666;margin-bottom:12px;font-size:13px">\u7528\u6237ID: <span id="puid"></span></p><div class="form-group"><label>\u65b0\u5bc6\u7801</label><input id="pnp" type="password" placeholder="\u81f3\u5c114\u4e2a\u5b57\u7b26"></div><button class="btn" onclick="pwok()">\u786e\u8ba4\u4fee\u6539</button><div id="pwmsg" style="display:none;padding:10px;border-radius:6px;margin-top:10px;font-size:14px;text-align:center"></div></div></div>
<script>
function pwdm(uid){document.getElementById('puid').textContent=uid;document.getElementById('pnp').value='';document.getElementById('pwmsg').style.display='none';document.getElementById('pwdm').style.display='flex'}
function pwok(){var np=document.getElementById('pnp').value,m=document.getElementById('pwmsg');m.style.display='none';if(np.length<4){m.textContent='\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26';m.style.color='#e74c3c';m.style.display='block';return}fetch('/admin/user/'+parseInt(document.getElementById('puid').textContent)+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:np})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='\u5df2\u4fee\u6539',m.style.color='#27ae60',setTimeout(function(){document.getElementById('pwdm').style.display='none'},1200)):(m.textContent=d.detail||'\u5931\u8d25',m.style.color='#e74c3c');m.style.display='block'})}
</script>"""
# Insert before </body> in _ADMIN
html = html.replace('</body>', modal + '\n</body>')

c = c[:start] + html + c[end:]

# Verify
import ast
ast.parse(c)
print(f'Final: {len(c)} bytes')
print(f'Over/Available: {len(c) - 86000} bytes')
print('Has pwdm:', 'pwdm' in c)
print('Has pwok:', 'pwok' in c)

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
