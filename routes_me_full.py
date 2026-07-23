import subprocess, sys
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')
lines = c.split('\n')

# get_me 函数
for i, l in enumerate(lines):
    if 'async def get_me' in l:
        print(f'=== get_me at line {i} ===')
        for j in range(i, min(i+20, len(lines))):
            print(f'{j}: {lines[j][:120]}')
        print()
        break

# 看 _ADMIN 模板开头
for i, l in enumerate(lines):
    if '_ADMIN' in l and ('=' in l):
        print(f'_ADMIN starts at line {i}: {l[:100]}')
        break

# 找用户表格行里的操作按钮
for i, l in enumerate(lines):
    if 'set-admin-btn' in l or 'set-id-btn' in l:
        print(f'user row btn at {i}: {l[:120]}')
        # 看周围几行
        for j in range(max(0,i-3), min(len(lines), i+8)):
            print(f'  {j}: {lines[j][:120]}')
        print()

# 看 _ADMIN 模板中各 UI 片段
# 找 loadUsers 的函数体
for i, l in enumerate(lines):
    if 'function loadUsers' in l or 'renderUsers' in l:
        print(f'loadUsers start at {i}: {l[:120][:120]}')
        # 打印后续20行
        for j in range(i, min(i+40, len(lines))):
            print(f'{j}: {lines[j][:120]}')
        print()
        break

# bb56d8f 的改密码路由
out2 = subprocess.check_output(['git', 'show', 'bb56d8f:railway_file_server.py'])
c2 = out2.decode('utf-8')
lines2 = c2.split('\n')
for i, l in enumerate(lines2):
    if '/me/change_password' in l:
        print(f'=== change_password route in bb56d8f (line {i}) ===')
        for j in range(i, min(i+14, len(lines2))):
            print(f'{j}: {lines2[j][:120]}')
        print()
        break

# 看 bb56d8f 的 admin 界面中改密码的 UI 片段
for i, l in enumerate(lines2):
    if 'cpwModal' in l or 'CPW' in l:
        print(f'bb56d8f cpw UI at {i}: {l[:120]}')
        break
