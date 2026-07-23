import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()

# Compress
lines = c.split('\n')
result = []
empty_run = 0
for line in lines:
    if not line.strip():
        empty_run += 1
        if empty_run <= 2:
            result.append('')
    else:
        empty_run = 0
        result.append(line)
c2 = '\n'.join(result)

# Find _ADMIN
p = c2.find('_ADMIN = """\\')
content_start = p + len('_ADMIN = """\\')
close = c2.find('html>"""', content_start) + len('html>"""')
admin_content = c2[content_start:close]
print(f'ADMIN content: {content_start}-{close}, {len(admin_content)} chars')

# Save compressed
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(c2)
print(f'Compressed: {len(c2)} bytes')
print(f'CONTENT_START={content_start}')
print(f'CONTENT_END={close}')
