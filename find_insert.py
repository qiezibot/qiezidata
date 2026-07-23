with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()
lines = c.split('\n')
for i,l in enumerate(lines):
    if l.startswith("@app.get('/me')"):
        print(f'{i}: {l}')
        for j in range(i+1, min(i+12, len(lines))):
            print(f'{j}: {lines[j][:100]}')
        break
print()
for i,l in enumerate(lines):
    if l.startswith("@app.get('/admin/stats')"):
        print(f'{i}: {l}')
        for j in range(max(0,i-8), i):
            print(f'{j}: {lines[j][:100]}')
        break
