import re
with open("railway_file_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"Total lines: {len(lines)}")
for i, l in enumerate(lines):
    ls = l.rstrip()
    # Find template variable assignments
    if ls.startswith("_LOGIN") or ls.startswith("_ADMIN") or ls.startswith("_USER"):
        print(f"Line {i+1}: {ls[:120]}")
    if 'TMPL' in ls and '=' in ls:
        print(f"Line {i+1}: {ls[:120]}")
