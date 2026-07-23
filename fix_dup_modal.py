import requests, json, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get file from GitHub
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
orig_len = len(content)
print(f'Original: {orig_len} bytes')

# Find the first (empty) profileModal div and mark it as style="display:none !important" 
# so it's effectively invisible and won't interfere
# The first one starts right after </script> line

# Strategy: find the FIRST occurrence and rename it to avoid conflict
old_div = '<div id="profileModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center">'
new_div = '<div id="profileModalDummy" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center">'

# Only replace the FIRST occurrence
new_content = content.replace(old_div, new_div, 1)
new_len = len(new_content)
print(f'New: {new_len} bytes')
print(f'Diff: {new_len - orig_len} bytes')

# Verify
count_old = new_content.count('id="profileModal"')
count_dummy = new_content.count('id="profileModalDummy"')
print(f'Remaining "profileModal": {count_old}')
print(f'Renamed to "profileModalDummy": {count_dummy}')

# Push
payload = {
    'message': 'Fix duplicate profileModal - rename first occurrence to profileModalDummy',
    'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push status: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
else:
    print(r2.text[:300])
