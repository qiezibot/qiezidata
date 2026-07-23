with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the missing decorator area
idx = content.find('async def script_cd_get')
# The decorator @app.get('/clouddata/{key}') should be right before it
before = content[idx-30:idx]
print(f"Before func: {repr(before)}")

# If decorator is missing, add it
if '@app.get' not in before:
    content = content[:idx] + "@app.get('/clouddata/{key}')\n" + content[idx:]
    print("Added missing decorator")
    
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print("py_compile OK!")
    
    # Verify
    import re
    for m in re.finditer(r"@app\.(get|post|delete)\('[^']*clouddata[^']*'\)", content):
        nxt = re.search(r'async def (\w+)', content[m.end():])
        fn = nxt.group(1) if nxt else '???'
        print(f"  {m.group(0):50s} -> {fn}")
else:
    print("Decorator present:", before)
