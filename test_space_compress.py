import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# 压缩空行
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

print(f'After empty line compress: {len(c)}')

# HTML compress
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
print(f'ADMIN: {start}-{end}')

html = c[start:end]

# Trim leading spaces
lines_h = html.split('\n')
lines_h = [l.lstrip() for l in lines_h]
html = '\n'.join(lines_h)

# Replace 3+ spaces with 1
# **But only inside <script> and <style> and text content**
# For now, skip this step to avoid issues
# html = re.sub(r'  +', ' ', html)

c2 = c[:start] + html + c[end:]
print(f'After HTML trim: {len(c2)}')

import ast
try:
    ast.parse(c2)
    print('Syntax OK (without space compress)')
except SyntaxError as e:
    print(f'Error: {e}')

# Now try with space compress
html2 = re.sub(r'  +', ' ', html)
c3 = c[:start] + html2 + c[end:]
print(f'With space compress: {len(c3)}')
try:
    ast.parse(c3)
    print('Syntax OK (with space compress)')
except SyntaxError as e:
    print(f'Error line {e.lineno}: {e.msg}')
    lines_c = c3.split('\n')
    for i in range(max(0,e.lineno-3), min(len(lines_c), e.lineno+2)):
        print(f'{i+1}: {repr(lines_c[i][:120])}')
