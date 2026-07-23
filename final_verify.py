import re
c = open('railway_file_server.py','r',encoding='utf-8').read()
i = c.find('function markCD')
print('markCD function:', 'found at', i if i>=0 else 'NOT FOUND')
cnt = sum(1 for _ in re.finditer(r'markCD', c))
print('Total markCD refs:', cnt)

# Verify routes
print()
for m in re.finditer(r"@app\.(get|post|delete)\('[^']*clouddata[^']*'\)", c):
    nxt = re.search(r'async def (\w+)', c[m.end():])
    fn = nxt.group(1) if nxt else '???'
    print(f'  {m.group(0):55s} -> {fn}')

print()
# Check Response import
assert 'Response,' in c, 'Missing Response in import!'
print('Response import: OK')
# Check clouddata_list uses db_fetch
assert 'await db_fetch(' in c[c.find('clouddata_list('):c.find('clouddata_list(')+400], 'clouddata_list uses db_fetch'
print('clouddata_list uses db_fetch: OK')
print('SIZE:', len(c))
print('ALL CHECKS PASSED')
