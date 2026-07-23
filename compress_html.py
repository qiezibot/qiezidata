import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

# 找 _ADMIN
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end = c.find('\n"""', start)
html = c[start:end]

# 把所有空白行去掉（但保留缩进和标签内的结构）
# 具体：连续空行合并为1个换行
cleaned = re.sub(r'\n\s*\n', '\n', html)
# 去掉行首尾空格（但不破坏 <pre> 或代码缩进）
# 这个要小心，JS 代码的缩进不能去掉
# 只修剪纯文本行
lines = cleaned.split('\n')
new_lines = []
for line in lines:
    # 如果行完全是空格、空白 HTML 文本
    if line.strip() == '':
        # 跳过多余空行
        if new_lines and new_lines[-1] == '':
            continue
        new_lines.append('')
    elif '<script>' in line or line.strip().startswith('var ') or line.strip().startswith('function ') or line.strip().startswith('}') or line.strip().startswith('async') or line.strip().startswith('if ') or line.strip().startswith('for(') or line.strip().startswith('fetch(') or line.strip().startswith('document'):
        # JS 代码不调整缩进
        new_lines.append(line)
    else:
        new_lines.append(line.rstrip())

compressed = '\n'.join(new_lines)
# 再去除连续空行
compressed = re.sub(r'\n{3,}', '\n\n', compressed)

print(f'Before: {len(html)} chars, {html.count(chr(10))} lines')
print(f'After: {len(compressed)} chars, {compressed.count(chr(10))} lines')
print(f'Saved: {len(html) - len(compressed)} chars')

# 写回
c = c[:start] + compressed + c[end:]
with open('railway_file_server_compressed.py', 'w', encoding='utf-8') as f:
    f.write(c)

# 检查语法
import ast
ast.parse(c)
print('Syntax OK')
