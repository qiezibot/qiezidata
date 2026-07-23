import difflib

with open('railway_file_server.py', encoding='utf-8') as f:
    clean = f.read()
with open('railway_file_server_modified.py', encoding='utf-8') as f:
    mod = f.read()

clean_lines = clean.split('\n')
mod_lines = mod.split('\n')

# 打印可读的 diff
diff = list(difflib.unified_diff(clean_lines, mod_lines, fromfile='clean', tofile='modified', lineterm=''))
for line in diff:
    print(line)
