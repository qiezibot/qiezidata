"""
Build compact password change UI that fits in ~1.6KB.
Strategy:
  1. Compress all templates (remove excessive blank lines) → ~84.4KB
  2. Modify _ADMIN minimally:
     a. Add "修改密码" button in user table rows (reuse existing onclick)
     b. Add modal HTML + tiny inline script before </body>
  3. Verify total < 86KB
"""
import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# Step 1: compress empty lines (keep max 2 consecutive)
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

# Step 2: Modify _ADMIN template
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 在 </thead> 之前加一列
replacements = [
    # 表格头加"操作"列
    (r'<th[^>]*>操作</th>', '<th>操作</th><th>修改密码</th>'),

    # 每行的删除按钮后加修改密码按钮（id=user.id）
    (r'onclick="deleteUser\(\$\{user\.id\}\)"', 
     'onclick="deleteUser(${user.id})" oncontextmenu="openPwdModal(${user.id});return false"'),

    # 原来没有"操作"列
]

# 直接用简单的字符串替换
# 1. 在"操作"标题后加一列
html = html.replace(
    '<th>\u64cd\u4f5c</th>',  # 操作
    '<th>\u64cd\u4f5c</th><th>\u5bc6\u7801</th>'  # 操作 | 密码
)

# 2. 在用户表每行的操作单元格后面加修改密码按钮
# 找到 ${user.id} 后面的 </td>
html = html.replace(
    'deleteUser(${user.id})">\u5220\u9664</button>',  # 删除
    'deleteUser(${user.id})">\u5220\u9664</button></td><td><a style="color:#667eea;cursor:pointer;font-size:13px" onclick="var u=this,id=u.dataset.uid||u.closest(\'tr\').querySelector(\'.user-id\').textContent;openPwdModal(Number(id))">\u6539\u5bc6</a></td>'  
    # "改密" + onclick 从 tr 中取 id
)

# 等等，这样复杂了。用更简单的方案：加一个带 "修改密码" 文本的列
# 更好的方式：在现有模板中找到</thead>和用户行

# 实际上原来的模板是什么结构？
# 我来看看用户表的大概内容

# 先侧边栏加点东西
html = html.replace(
    'data-page="page-users"',
    'data-page="page-users" onclick="switchPage(\'page-users\',this)"'
)

# 看看现有的表格结构（找 rows 循环）
rows_pos = html.find('${user.id}')
if rows_pos > 0:
    print(f'Found user.id at pos {rows_pos}')
    print(html[rows_pos-200:rows_pos+200])
else:
    print('user.id not found!')
