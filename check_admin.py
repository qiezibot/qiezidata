import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 检查 _ADMIN 完整性
m = re.search(r'_ADMIN\s*=\s*"""', c)
if m:
    rest = c[m.end():]
    end_pos = rest.find('\n"""')
    if end_pos > 0:
        print(f'_ADMIN OK: {end_pos} chars')
    else:
        print('WARNING: _ADMIN never closes')
        print(rest[:100])
        print('...')
        print(rest[-200:])
else:
    print('No _ADMIN found')

# 找所有 """ 出现位置
triple_quotes = [m.start() for m in re.finditer(r'"""', c)]
print(f'Total triple quotes: {len(triple_quotes)}')
