import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

admin_pat = re.compile(r'_ADMIN = """\\(.*?)"""\n\n_USER = """\\', re.DOTALL)
m = admin_pat.search(content)
t = m.group(1)

# Find the JS section for My Files in admin
idx = t.find('loadMyFiles')
print(f"loadMyFiles at {idx}")
print(repr(t[idx:idx+800]))
