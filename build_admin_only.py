import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# Step 1: Compress
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

# Compress HTML in _ADMIN (only inside the triple-quoted string, not Python)
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]
# Remove leading spaces from each line (safe for HTML in raw string)
lines_h = html.split('\n')
lines_h = [l.lstrip() for l in lines_h]
html = '\n'.join(lines_h)
# Compress 3+ spaces to 1 (only when not inside <pre>/<code>/<script>/<style>)
# Simple: compress across entire HTML, which is fine since this is a template
html = re.sub(r'  +', ' ', html)
c = c[:start] + html + c[end:]

print(f'Compressed: {len(c)} bytes')

# Step 2: Add admin change password - only
# 2a: Add "密码" header column
html = c[start:end]
html = html.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')

# 2b: Add button to user rows - in loadUsers render 
old1 = ")+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new1 = ")+'</td>'+'<td><a style=color:#667eea;cursor:pointer onclick=aCP('+u.id+')>\u6539\u5bc6</a></td></tr>'}document.getElementById('userTableBody').innerHTML=h"
html = html.replace(old1, new1)

# 2c: Same for deleteUser render
old2 = ")+'</td></tr>'}document.getElementById('myFileList').innerHTML=h"
new2 = ")+'</td>'+'<td><a style=color:#667eea;cursor:pointer onclick=aCP('+u.id+')>\u6539\u5bc6</a></td></tr>'}document.getElementById('myFileList').innerHTML=h"
html = html.replace(old2, new2)

# 2d: Add modal + script
modal = '<div id=cpModal class=modal style=display:none><div class=modal-content style=max-width:360px><span class=close onclick="this.parentElement.parentElement.style.display=\'none\'">&times;</span><h3>\u4fee\u6539\u5bc6\u7801</h3><div class=fg><label>\u65b0\u5bc6\u7801</label><input id=cpNP type=password></div><button class=btn onclick=cpW()>\u786e\u8ba4</button><div id=cpM class=msg></div></div></div><script>function aCP(u){cpModal.style.display="flex";cpNP.value="";cpM.style.display="none"}function cpW(){var n=cpNP.value,m=cpM;m.style.display="none";if(n.length<4){m.textContent="\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26";m.style.display="block";return}fetch("/admin/user/"+_cu+"/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent="\u5df2\u4fee\u6539",m.style.color="#27ae60",setTimeout(function(){cpModal.style.display="none"},1200)):(m.textContent=d.detail||"\u5931\u8d25",m.style.color="#e74c3c");m.style.display="block"})}var _cu=0;</script>'
html = html.replace('</body>', modal + '\n</body>')

c = c[:start] + html + c[end:]

print(f'Final: {len(c)} bytes')
if len(c) > 86000:
    print(f'OVER by {len(c) - 86000} - need to trim')
else:
    print(f'Under! Free: {86000 - len(c)}')

import ast
ast.parse(c)
print('Syntax OK')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
