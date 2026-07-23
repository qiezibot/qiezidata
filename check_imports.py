import re

for name in ['railway_file_server.py', 'railway_file_server_modified.py']:
    with open(name, encoding='utf-8') as f:
        c = f.read()
    print(f'\n=== {name} ({len(c)} bytes) ===')
    # 提取所有 import
    for m in re.finditer(r'^(?:from\s+\S+\s+)?import\s+.+', c, re.MULTILINE):
        line = m.group().strip()
        print(f'  {line}')
