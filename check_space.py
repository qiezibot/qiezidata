import re

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]
lines = html.split('\n')
empty = sum(1 for l in lines if not l.strip())
print(f'Template: {len(html)} chars, {len(lines)} lines, {empty} empty')
lines_all = c.split('\n')
empty_all = sum(1 for l in lines_all if not l.strip())
print(f'File: {len(c)} chars, {len(lines_all)} lines, {empty_all} empty')
