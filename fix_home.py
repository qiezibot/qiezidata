import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current file
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Current size: {len(content)}, SHA: {sha}')

# Find home() and replace ENTIRE function
home_func = content.find('async def home(request: Request):')
next_func = content.find('async def ', home_func + 10)
if next_func < 0:
    next_func = content.find('@app.', home_func + 10)

print(f'home() from {home_func} to {next_func}')
print(f'Current home body:')
print(repr(content[home_func:next_func])[:800])

# Replace entire home function
new_home = '''async def home(request: Request):


    uid = _auth(request)


    if uid is None: return HTMLResponse(_LOGIN)


    user = await _user(uid)


    if not user: return HTMLResponse(_LOGIN)


    name = user.get('display_name','') or user.get('username','')


    admin_template = _ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', ''))
    try:
        admin_template.encode('utf-8')
    except UnicodeEncodeError:
        admin_template = _ADMIN.encode('utf-8', errors='replace').decode('utf-8').replace('<!--U-->', name).replace('<!--R-->', user.get('role', ''))
    return HTMLResponse(admin_template)


'''

content = content[:home_func] + new_home + content[next_func:]

# Verify Python syntax
import py_compile, tempfile, os
final = content.encode('utf-8')
tmp = tempfile.NamedTemporaryFile(suffix='.py', delete=False)
tmp.write(final)
tmp.close()
try:
    py_compile.compile(tmp.name, doraise=True)
    print('Python syntax OK')
except Exception as e:
    print(f'Python syntax error: {e}')
    with open(tmp.name, 'r') as f:
        lines = f.readlines()
    for i in range(max(0, home_func-5), min(len(lines), home_func + 30)):
        print(f'  {i+1}: {lines[i].rstrip()}')
os.unlink(tmp.name)

# Push
payload = {
    'message': 'Fix home() - safe encoding fallback for non-BMP chars',
    'content': base64.b64encode(final).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Status: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
else:
    print(r2.text[:300])
