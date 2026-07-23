import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = __import__('re').search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = __import__('re').search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 function loadUsers
pos = html.find('function loadUsers')
if pos < 0:
    pos = html.find('loadUsers=function')
if pos < 0:
    pos = html.find('loadUsers()')
print(f'loadUsers at {pos}')
print(html[pos:pos+3000])
