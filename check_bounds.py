import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
print(f'Start: {start}')
pos = c.find('html>"""', start)
if pos >= 0:
    print(f'End at {pos}: {repr(c[pos-20:pos+15])}')
else:
    print('html>""" not found')
