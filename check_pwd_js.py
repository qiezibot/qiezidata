import re

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'return PlainTextResponse', c)
start = m.end() + 1  # after the (
# find ''' or """
if "'''" in c[start:start+5]:
    start += 3
    end = c.find("'''", start)
else:
    start += 3
    end = c.find('"""', start)

js = c[start:end]
print(f'JS in route: {len(js)} chars')
print(f'Has openProfile: {"openProfile" in js}')
print(f'Has submitAdmin: {"submitAdmin" in js}')
print(f'Has profileModal HTML: {"profileModal" in js}')
print(f'First 100: {js[:100]}')
print(f'Last 50: {js[-50:]}')
