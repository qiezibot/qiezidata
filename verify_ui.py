import re
with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== Clouddata Routes ===')
for m in re.finditer(r"@app\.(get|post|delete)\('[^']*clouddata[^']*'\)", content):
    nxt = re.search(r'async def (\w+)', content[m.end():])
    fn = nxt.group(1) if nxt else '???'
    print(f"  {m.group(0):55s} -> {fn}")

print()
print('=== UI Checks ===')
checks = ['exportCD','markCD','delCloudData','loadCloudData','addCloudData',
          '\u5bfc\u51fa\u5168\u90e8','\u5bfc\u51fa\u5df2\u8bfb','\u5bfc\u51fa\u672a\u8bfb',
          '\u6807\u5df2\u8bfb','\u6807\u672a\u8bfb','\u72b6\u6001']
for c in checks:
    print(f"  '{c}': {c in content}")

print()
print('Size:', len(content))
