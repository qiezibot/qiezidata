import subprocess
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')
lines = c.split('\n')

# 找用户表格 HTML 模板和 loadUsers 完整内容
capture = False
capture_lines = 0
seen_loadusers = False
for i, l in enumerate(lines):
    # 找到 loadUsers 函数
    if 'async function loadUsers' in l:
        seen_loadusers = True
        capture = True
        capture_lines = 0
        print(f'--- loadUsers starts at {i} ---')
    if seen_loadusers and capture:
        print(f'{i}: {l}')
        capture_lines += 1
        if capture_lines > 60:
            break

print()
print('=== user table HTML template ===')
# 找表格行 template
for i, l in enumerate(lines):
    if 'innerHTML' in l and 'tr' in l and ('uid' in l or 'username' in l):
        print(f'{i}: {l[:140]}')
        for j in range(max(0,i-1), min(len(lines), i+12)):
            print(f'  {j}: {lines[j][:140]}')
        print()
