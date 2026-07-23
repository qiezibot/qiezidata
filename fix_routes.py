# Fix route order: export before get by key
# Move script_cd_export function body before script_cd_get

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The order we want:
# 1. POST /clouddata (upsert)
# 2. GET /clouddata (list, with ?key=)
# 3. GET /clouddata/export/{mode}
# 4. GET /clouddata/{key}
# 5. DELETE /clouddata/{key}
# 6. POST /clouddata/mark/{key}
# 7. POST /clouddata/mark/id/{cid}

# Currently list -> get -> export -> delete -> mark -> mark_id
# Need list -> export -> get -> delete -> mark -> mark_id

list_start = content.find('async def script_cd_list')
get_start = content.find('async def script_cd_get')
export_start = content.find('async def script_cd_export')
delete_start = content.find('async def script_cd_delete')

# Extract export block
export_block = content[get_start:export_start]  # from 'async def script_cd_get' to just before 'async def script_cd_export'
# Actually pick the function from its decorator to next decorator
# Find decorator for script_cd_get
get_decorator = content.rfind('@app.get', 0, get_start)
get_decorator = content.rfind('@app.get', 0, get_decorator - 1)  # second-to-last @app.get before get start
export_decorator = content.rfind('@app.get', 0, export_start)
# The export function starts at export_decorator and ends at before the next decorator
export_func_end = content.find('\n\n\n', export_decorator)
get_func_end = content.find('\n\n\n', get_decorator)

# Swap: replace get section with export section and vice versa
print(f"get_decorator={get_decorator}, get_func_end={get_func_end}")
print(f"export_decorator={export_decorator}, export_func_end={export_func_end}")

get_section = content[get_decorator:get_func_end]
export_section = content[export_decorator:export_func_end]

# Replace get section with export
content = content[:get_decorator] + export_section + content[get_func_end:]
# Now the old export section still exists - replace it with the old get section
# But the positions have shifted!
new_export_start = content.find(export_section, get_decorator) + len(export_section)
old_export_now = content.find(export_section, new_export_start)
if old_export_now > 0:
    content = content[:old_export_now] + get_section + content[old_export_now + len(export_section):]

with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Size: {len(content)} bytes")

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print("py_compile OK!")

# Check route order
import re
for m in re.finditer(r"@app\.(get|post|delete)\('([^']+)'\)", content):
    # Get next async def
    rest = content[m.end():]
    nxt = re.search(r'async def (\w+)', rest)
    fn = nxt.group(1) if nxt else '???'
    if 'clouddata' in m.group(2) or 'clouddata' in fn:
        print(f"  {m.group(1).upper():6s} {m.group(2):30s} -> {fn}")
