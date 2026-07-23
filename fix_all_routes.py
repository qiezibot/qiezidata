import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check which decorators are missing
missing = []
for fn, route in [('script_cd_delete', "@app.delete('/clouddata/{key}')"),
                  ('script_cd_mark', "@app.post('/clouddata/mark/{key}')")]:
    idx = content.find('async def ' + fn)
    before = content[idx-40:idx]
    print(f"Before {fn}: {repr(before)}")
    if '@app' not in before:
        # Add decorator
        content = content[:idx] + route + '\n' + content[idx:]
        print(f"  Added {route}")
        missing.append(fn)

if missing:
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print("py_compile OK!")

    # Final check
    for m in re.finditer(r"@app\.(get|post|delete)\('[^']*clouddata[^']*'\)", content):
        nxt = re.search(r'async def (\w+)', content[m.end():])
        fn = nxt.group(1) if nxt else '???'
        print(f"  {m.group(0):50s} -> {fn}")
else:
    print("All decorators present!")
