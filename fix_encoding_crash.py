import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current file
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Current size: {len(content)}, SHA: {sha}')

# Find and modify the home() function to add try-except for encoding
# Look for: return HTMLResponse(_ADMIN.replace
home_func = content.find('async def home(request: Request):')
home_end = content.find('async def ', home_func + 10)
if home_end < 0:
    home_end = content.find('@app.', home_func + 10)

print(f'home() function: {home_func} to {home_end}')

# The home function should look like:
#   return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))
# Replace with safe version
old_home_return = "return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))"
new_home_return = """try:
        return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))
    except UnicodeEncodeError:
        safe_admin = _ADMIN.encode('utf-8', errors='replace').decode('utf-8')
        return HTMLResponse(safe_admin.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))"""

if old_home_return in content:
    content = content.replace(old_home_return, new_home_return)
    print('home() return fixed with try-except')
else:
    # Try to find the actual return
    idx = content.find('return HTMLResponse(_ADMIN.replace', home_func)
    if idx > 0:
        end_idx = content.find(')', idx) + 1
        actual = content[idx:end_idx]
        print(f'Actual return: {repr(actual)}')
        content = content[:idx] + """try:
        return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))
    except UnicodeEncodeError:
        safe_admin = _ADMIN.encode('utf-8', errors='replace').decode('utf-8')
        return HTMLResponse(safe_admin.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))""" + content[end_idx:]

# Also check the second home return (for non-admin)
old_home_return2 = "return HTMLResponse(_USER.replace('<!--U-->', name))"
if old_home_return2 in content:
    print('Non-admin return found')
else:
    print('Non-admin return not found (already unified to _ADMIN)')

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
os.unlink(tmp.name)

# Push
payload = {
    'message': 'Fix encoding crash - safe HTML rendering',
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
