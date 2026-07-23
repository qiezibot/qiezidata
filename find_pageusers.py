import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = __import__('re').search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = __import__('re').search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 page-users 部分
pu = html.find('page-users')
print(f'page-users at {pu}')
if pu >= 0:
    print(html[pu:pu+2000])
