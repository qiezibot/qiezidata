import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 1. 压缩整个文件：超过2个连续空行的缩到2个
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

compressed = '\n'.join(result)
print(f'Original: {len(c)} chars, {len(lines)} lines')
print(f'Compressed: {len(compressed)} chars, {len(result)} lines')
print(f'Saved: {len(c) - len(compressed)} chars')

# 写回到 railway_file_server.py
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(compressed)

import ast
ast.parse(compressed)
print('Syntax OK')
