import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# Step 1: Only compress empty lines — NOT HTML whitespace
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
print(f'Compressed: {len(c)} bytes')

# Step 2: Precise _ADMIN boundaries
m = re.search(r'_ADMIN\s*=\s*"""', c)
content_start = m.end() + 1  # skip the first \ after """
close_pos = c.find('html>"""', content_start)
content_end = close_pos
html = c[content_start:content_end]
print(f'ADMIN: {content_start}-{content_end}, {len(html)} chars')

# Step 3: Minimal changes to HTML template only
# 3a: Add "密码" header column
html = html.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')

# 3b: Add "改密" link in user table rows (loadUsers render)
old1 = ")+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new1 = ")+'</td>'+'<td><a onclick=aCP('+u.id+') style=color:#667eea;cursor:pointer>\u6539\u5bc6</a></td></tr>'}document.getElementById('userTableBody').innerHTML=h"
html = html.replace(old1, new1)

# 3c: Same for deleteUser render
old2 = ")+'</td></tr>'}document.getElementById('myFileList').innerHTML=h"
new2 = ")+'</td>'+'<td><a onclick=aCP('+u.id+') style=color:#667eea;cursor:pointer>\u6539\u5bc6</a></td></tr>'}document.getElementById('myFileList').innerHTML=h"
html = html.replace(old2, new2)

# 3d: Minimal modal + script (no CSS — reuse existing .modal class from template)
modal = '<div id=cpM class=modal style=display:none><div class=modal-content style=max-width:360px><span onclick="document.getElementById('+"'"+'cpM'+"'"+').style.display='+"'"+'none'+"'"+'" style=float:right;font-size:22px;cursor:pointer>&times;</span><h3>\u4fee\u6539\u7528\u6237\u5bc6\u7801</h3><div class=form-group><label>\u65b0\u5bc6\u7801</label><input id=cpNP type=password></div><button onclick=cpW() class=btn>\u786e\u8ba4\u4fee\u6539</button><div id=cpE style=display:none></div></div></div><script>var _cu=0;function aCP(u){_cu=u;document.getElementById('+"'"+'cpM'+"'"+').style.display='+"'"+'flex'+"'"+';document.getElementById('+"'"+'cpNP'+"'"+').value='+"'"+'"}function cpW(){var n=document.getElementById('+"'"+'cpNP'+"'"+').value,m=document.getElementById('+"'"+'cpE'+"'"+');m.style.display='+"'"+'none'+"'"+';if(n.length<4){m.textContent='+"'"+'\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26'+"'"+';m.style.display='+"'"+'block'+"'"+';return}fetch('+"'"+'/admin/user/'+"'"+'+_cu+'+"'"+'/change_password'+"'"+',{method:'+"'"+'POST'+"'"+',credentials:'+"'"+'include'+"'"+',headers:{'+"'"+'Content-Type'+"'"+':'+"'"+'application/json'+"'"+'},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(m.textContent='+"'"+'\u5df2\u4fee\u6539'+"'"+',m.style.color='+"'"+'#27ae60'+"'"+',setTimeout(function(){document.getElementById('+"'"+'cpM'+"'"+').style.display='+"'"+'none'+"'"+'},1200)):(m.textContent=d.detail||'+"'"+'\u5931\u8d25'+"'"+',m.style.color='+"'"+'#e74c3c'+"'"+');m.style.display='+"'"+'block'+"'"+'})}</script>'
html = html.replace('</body>', modal + '\n</body>')

c = c[:content_start] + html + c[content_end:]

import ast
ast.parse(c)
print(f'Final: {len(c)} bytes')
print(f'Free: {86000 - len(c)}')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
