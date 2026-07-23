# 提取 modified 版本的 init_db 函数
import re

name = 'railway_file_server_modified.py'
with open(name, encoding='utf-8') as f:
    c = f.read()

# 找 init_db
start = c.find('async def init_db()')
if start < 0:
    print('init_db not found')
else:
    # 直到下一个异步函数
    rest = c[start:]
    m = re.search(r'\nasync def ', rest)
    if m:
        end = start + m.start()
        func = c[start:end]
        print(f'init_db() at {start}-{end}, {len(func)} chars')
        print('='*50)
        print(func)
