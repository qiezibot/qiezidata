import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = __import__('re').search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = __import__('re').search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

for term in ['loadUsers', 'deleteUser', 'fetch']:
    pos = html.find(term)
    if pos >= 0:
        print(f'==={term}===')
        print(html[max(0,pos-100):pos+500])
        print()
