import re
with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

for m in re.finditer(r"@app\.(get|post|delete)\('[^']*clouddata[^']*'\)", content):
    nxt = re.search(r'async def (\w+)', content[m.end():])
    fn = nxt.group(1) if nxt else '???'
    print(f"{m.group(0):50s} -> {fn}")

print()
# Check export uses Response
ei = content.find('async def script_cd_export')
print(f"export func: {ei}")
print(content[ei:ei+200])
print()
# Check Response import
ci = content.find('from fastapi.responses import')
print(content[ci:ci+120])
