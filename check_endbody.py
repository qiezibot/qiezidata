import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
em = re.search(r'\n"""', c[start:])
end = start + em.start()
html = c[start:end]
print('Has </body>:', '</body>' in html)
print('Has </html>:', '</html>' in html)
print('Last 200:', repr(html[-200:]))
