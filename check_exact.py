import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

admin_pat = re.compile(r'_ADMIN = """\\(.*?)"""\n\n_USER = """\\', re.DOTALL)
m = admin_pat.search(content)
t = m.group(1)

# Search for various confirm patterns
for pat in ['confirm', 'Delete', 'delete', 'if(!confirm', 'confirm(']:
    idx = t.find(pat)
    if idx >= 0:
        print(f"'{pat}' at {idx}: {repr(t[idx-5:idx+30])}")
    else:
        print(f"'{pat}' NOT found")

# Search for toast patterns
for pat in ["Toast('", "Uploaded", "Failed", "Deleted"]:
    idx = t.find(pat)
    if idx >= 0:
        print(f"'{pat}' at {idx}: {repr(t[idx-5:idx+30])}")
    else:
        # try different encoding
        print(f"'{pat}' NOT found")

# Search for filelist 'No files'
idx2 = t.find('No files')
if idx2 >= 0:
    print(f"'No files' at {idx2}: ctx={repr(t[idx2-10:idx2+30])}")
else:
    idx2 = t.find('no files')
    print(f"'no files' NOT found")

# Check for 'None' in different contexts
idx3 = t.find('>None<')
if idx3 >= 0:
    print(f"'>None<' at {idx3}: ctx={repr(t[idx3-20:idx3+20])}")
else:
    print("'>None<' NOT found")
idx4 = t.find("'None'")
if idx4 >= 0:
    print(f"'None' at {idx4}: ctx={repr(t[idx4-20:idx4+30])}")
else:
    print("'None' NOT found")
