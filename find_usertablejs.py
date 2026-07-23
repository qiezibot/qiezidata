import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 userTableBody 相关的 JS
pos = html.find('userTableBody')
if pos >= 0:
    # 向后找，看怎么填充 tbody
    print(html[pos:pos+2000])
