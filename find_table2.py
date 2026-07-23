import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# Find the user table
for keyword in ['${', 'user', 'table', 'thead', 'tbody', 'users']:
    pos = html.find(keyword)
    if pos >= 0:
        snippet = html[pos:pos+800]
        print(f'--- Found "{keyword}" at pos {pos} ---')
        print(snippet[:400])
        print('...')
        print(snippet[-200:])
        print()
        break
