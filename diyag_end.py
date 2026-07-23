import re

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()

# 检查 _ADMIN 结束附近
print(f'End marker at {end}: {repr(c[end:end+20])}')
# 看看有没有第二个 """
second = c[end+20:].find('"""')
if second >= 0:
    print(f'Second """ at offset {second}: {repr(c[end+20+second:end+50+second])}')
