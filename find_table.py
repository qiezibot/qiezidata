import re

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找表格相关的内容
for keyword in ['${', 'user', 'table', 'thead', 'tbody', 'for']:
    pos = html.find('${')
    if pos >= 0:
        print(f'--- Found ${{ at pos {pos} ---')
        print(html[pos-300:pos+500])
        break

if pos < 0:
    # 找 users.map
    pos = html.find('users')
    if pos >= 0:
        print(f'--- users at {pos} ---')
        print(html[pos:pos+500])
