import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 /api/users 或用户渲染相关的 JS
for term in ['api/users', 'userTableBody', 'loadUsers', 'fetch.*user']:
    pos = html.find(term)
    if pos >= 0:
        print(f'*** Found "{term}" at pos {pos} ***')
        print(html[pos:pos+2000])
        print()
        break
