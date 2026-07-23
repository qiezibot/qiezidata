import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# 压缩
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

# 定位 _ADMIN
m = re.search(r'_ADMIN\s*=\s*"""', c)
content_start = m.end() + 1  # skip \ after """
close_pos = c.find('html>"""', content_start)
content_end = close_pos
html = c[content_start:content_end]

# Trim leading spaces + compress spaces (已验证 OK)
lines_h = html.split('\n')
lines_h = [l.lstrip() for l in lines_h]
html = '\n'.join(lines_h)
html = re.sub(r'  +', ' ', html)

# ===== 改密码 UI =====

# 1. 表格头加"密码"列
html = html.replace('<th>\u64cd\u4f5c</th>', '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>')

# 2. 用户行渲染加"改密"按钮（loadUsers 函数里）
old1 = ")+'</td></tr>'}document.getElementById('userTableBody').innerHTML=h"
new1 = ")+'</td>'+'<td><a onclick=aCP('+u.id+') style=color:#667eea;cursor:pointer>\u6539\u5bc6</a></td></tr>'}document.getElementById('userTableBody').innerHTML=h"
html = html.replace(old1, new1)

# 3. deleteUser 里的渲染
old2 = ")+'</td></tr>'}document.getElementById('myFileList').innerHTML=h"
new2 = ")+'</td>'+'<td><a onclick=aCP('+u.id+') style=color:#667eea;cursor:pointer>\u6539\u5bc6</a></td></tr>'}document.getElementById('myFileList').innerHTML=h"
html = html.replace(old2, new2)

# 4. 模态框 + JS（紧）
modal = '<div id=cpM class=modal style=display:none><div class=modal-content style=max-width:360px><span onclick=\'cpM.style.display="none"\' style=float:right;font-size:22px;cursor:pointer>&times;</span><h3>\u4fee\u6539\u5bc6\u7801</h3><div class=fg><label>\u65b0\u5bc6\u7801</label><input id=cpNP type=password></div><button onclick=cpW() class=btn>\u786e\u8ba4</button><div id=cpE class=msg></div></div></div><script>var _c=0;function aCP(u){_c=u;cpM.style.display="flex";cpNP.value="";cpE.style.display="none"}function cpW(){var n=cpNP.value;cpE.style.display="none";if(n.length<4){cpE.textContent="\u5bc6\u7801\u81f3\u5c114\u4e2a\u5b57\u7b26";cpE.style.display="block";return}fetch("/admin/user/"+_c+"/change_password",{method:"POST",credentials:"include",headers:{"Content-Type":"application/json"},body:JSON.stringify({new_password:n})}).then(function(r){return r.json()}).then(function(d){d.ok?(cpE.textContent="\u5df2\u4fee\u6539",cpE.style.color="#27ae60",setTimeout(function(){cpM.style.display="none"},1200)):(cpE.textContent=d.detail||"\u5931\u8d25",cpE.style.color="#e74c3c");cpE.style.display="block"})}</script>'
html = html.replace('</body>', modal + '\n</body>')

c = c[:content_start] + html + c[content_end:]

# Verify
import ast
ast.parse(c)
print(f'Final: {len(c)} bytes')
print(f'Available: {86000 - len(c)}')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c)
