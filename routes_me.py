import subprocess, sys
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')
lines = c.split('\n')

# 看 /me GET
for i, l in enumerate(lines):
    if '@app.get' in l and 'me' in l:
        print(f'=== /me GET at line {i} ===')
        for j in range(i, min(i+10, len(lines))):
            print(f'{j}: {lines[j][:120]}')
        print()

# 看 set_id / set_admin 回调
for i, l in enumerate(lines):
    if 'set_admin' in l or 'set_id' in l:
        next_10 = []
        for j in range(i, min(i+6, len(lines))):
            next_10.append(f'{j}: {lines[j][:120]}')
        print('\n'.join(next_10))
        print()
