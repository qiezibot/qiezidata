import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()

# 找所有 _ADMIN 相关的等号和引号
for m in re.finditer(r'_ADMIN\s*=\s*"""', c):
    print(f'=_ADMIN at {m.start()}')
    print(c[m.start():m.start()+100])
    print()

# 找所有可能的 """
for m in re.finditer(r'"""', c):
    print(f'"""{m.start()}: {repr(c[m.start()-5:m.start()+30])}')
