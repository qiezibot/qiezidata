import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# 压缩
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

# 只压缩 _ADMIN 内部 HTML 的空格（不碰 Python 区域）
# 但 _ADMIN 是纯文本，它的缩进都是 HTML 缩进
# re.sub(r'  +', ' ', html) 不应该影响语法
# 问题是：压缩后 _ADMIN 内部有空行 break 了代码缩进吗？
# 检查最后一段 _ADMIN 前有没有 Python 代码依赖缩进

# 直接 ast.parse 看看
import ast
try:
    ast.parse(c)
    print('OK')
except SyntaxError as e:
    print(f'Error at line {e.lineno}: {e.msg}')
    if e.lineno:
        lines = c.split('\n')
        for i in range(max(0,e.lineno-3), min(len(lines), e.lineno+2)):
            print(f'{i+1}: {repr(lines[i][:100])}')
