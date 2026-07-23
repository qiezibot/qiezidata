import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current file
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Current size: {len(content)}, SHA: {sha}')

# Fix non-BMP chars in _ADMIN template
adm_start = content.find('_ADMIN = """')
adm_start_content = content.index('"""', adm_start) + 3
adm_end = content.find('"""\n\n\n\n\n\n\n\n\n\n\n\n\n# ---- CloudData', adm_start_content)
if adm_end < 0:
    adm_end = content.find('"""\n\n# ---- CloudData', adm_start_content)

print(f'ADMIN: {adm_start_content} to {adm_end}')
adm = content[adm_start_content:adm_end]

# Replace all non-BMP emoji with HTML entities
count = 0
result_chars = []
for ch in adm:
    if ord(ch) > 0xFFFF:
        result_chars.append(f'&#x{ord(ch):x};')
        count += 1
    else:
        result_chars.append(ch)
adm = ''.join(result_chars)
print(f'Replaced {count} non-BMP chars')

result = content[:adm_start_content] + adm + content[adm_end:]

# Verify
final = result.encode('utf-8')
print(f'Final size: {len(final)}')

# Verify no surrogates
text = final.decode('utf-8', errors='surrogateescape')
surrogates = sum(1 for ch in text if 0xD800 <= ord(ch) <= 0xDFFF)
print(f'Surrogates in result: {surrogates}')

# Push
payload = {
    'message': 'Fix surrogate - emoji to HTML entities',
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
