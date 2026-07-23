c=open('railway_file_server.py','r',encoding='utf-8').read()
start = c.find('function loadCloudDataProjects')
end_str = 'document.addEventListener('
end = c.find(end_str, start)
end = c.find(';', end) + 1
js_section = c[start:end]

# Check single-quote inside single-quoted strings
# The issue might be: we have JS strings like '...' that contain escaped '
# But if the \' isn't properly handled...
import re
for m in re.finditer(r"\'", js_section):
    ctx = js_section[max(0,m.start()-5):m.start()+5]
    if m.start() > 0 and js_section[m.start()-1] == '\\':
        continue  # properly escaped
    print(f'SINGLE QUOTE at {m.start()}: ...{repr(ctx)}...')

# Check if there's an extra single-quote breaking things
# Count single quotes
sq = sum(1 for m in re.finditer("'", js_section))
print(f'Total single quotes: {sq}')
dq = sum(1 for m in re.finditer('"', js_section))
print(f'Total double quotes: {dq}')

# Show the last 200 chars of js_section
print('\nLast 200 chars:')
print(repr(js_section[-200:]))
