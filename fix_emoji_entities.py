import requests, json, base64

token = 'ghp_lOX0KYIQoBh9kt4wXtrWzu8uWrVclz3ODBGZ'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current file
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Current size: {len(content)}, SHA: {sha}')

# Fix: Remove any non-BMP characters from _ADMIN template.
# The server has issues with surrogates. Replace emoji with HTML entities.
adm_start = content.find('_ADMIN = """')
adm_marker = '"""'
adm_start_content = content.index(adm_marker, adm_start) + 3
adm_end = content.find('"""\n\n\n\n\n\n\n\n\n\n\n\n\n# ---- CloudData', adm_start_content)
if adm_end < 0:
    adm_end = content.find('"""\n\n# ---- CloudData', adm_start_content)

print(f'ADMIN: {adm_start_content} to {adm_end}')

adm = content[adm_start_content:adm_end]

# The issue might be non-BMP characters in the template when server processes them
# Replace actual emoji with their HTML entities
import re

# Find non-BMP chars (emoji, etc.)
non_bmp_chars = set()
for i, ch in enumerate(adm):
    if ord(ch) > 0xFFFF:
        non_bmp_chars.add(ch)
        entity = f'&#x{ord(ch):x};'
        adm = adm.replace(ch, entity)
        print(f'  Replaced U+{ord(ch):04X} at pos {i}')

print(f'Replaced {len(non_bmp_chars)} unique non-BMP characters')

# Rebuild
result = content[:adm_start_content] + adm + content[adm_end:]

# Save and push
with open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'w', encoding='utf-8') as f:
    f.write(result)

# Verify
final_check = result.encode('utf-8')
print(f'Final size: {len(final_check)}')

# Push
payload = {
    'message': 'Fix surrogate issue - replace emoji with HTML entities',
    'content': base64.b64encode(final_check).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push status: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json().get("commit",{}).get("sha","N/A")}')
else:
    print(r2.json().get('message',''))
