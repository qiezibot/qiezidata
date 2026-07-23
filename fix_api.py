# Fix: rename db_exec -> db_execute, deduplicate clouddata APIs
with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix all db_exec( -> db_execute(
content = content.replace('db_exec(', 'db_execute(', 8)

# 2. Remove duplicate clouddata API block
# Find the two blocks - keep the first one (with better SQL), remove the second
first_idx = content.find("@app.get('/admin/clouddata')")
second_idx = content.find("@app.get('/admin/clouddata')", first_idx + 50)
if second_idx > 0:
    # Find where second block ends (before the next @app.get)
    next_route = content.find("@app.get('/admin/stats')", second_idx)
    if next_route > 0:
        dup_block = content[second_idx:next_route]
        content = content[:second_idx] + content[next_route:]
        print(f"Removed duplicate block ({len(dup_block)} chars)")

# 3. Verify single copies
for fn in ['clouddata_list', 'clouddata_add', 'clouddata_del']:
    cnt = content.count(fn)
    print(f'{fn}: {cnt}')
    if cnt != 1:
        print(f"  WARNING: expected 1, found {cnt}")

# Verify no db_exec without 'ute'
import re
stray = list(re.finditer(r'\bdb_exec\b(?!ute)', content))
print(f'Stray db_exec: {len(stray)}')

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Size: {len(content)} bytes")
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")
