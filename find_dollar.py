import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = __import__('re').search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = __import__('re').search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 '${' 和 'users' 附近的内容
dollar = html.find('${')
print(f'${{ at pos {dollar}')
if dollar >= 0:
    # 往回找表格
    print(html[dollar-200:dollar+300])
