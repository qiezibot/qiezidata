import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
print(f'Size: {len(content)}, SHA: {sha}')

# Find _ADMIN
adm_marker = '_ADMIN = """'
adm_start = content.find(adm_marker)
adm_content_start = content.index('"""', adm_start) + 3
print(f'Marker at {adm_start}, content start at {adm_content_start}')

# More flexible end detection
# Look for triple quotes after content_start
triple = content.find('"""', adm_content_start)
print(f'First triple quote after content: {triple}, chars: {repr(content[triple:triple+100])}')

# Actually _ADMIN goes until before # ---- CloudData
# Let's check what's after the first """
after_first = content[adm_content_start:adm_content_start+200]
print(f'First 200 chars of admin: {repr(after_first)}')

# Find the right closing """
# Look for """ followed by newlines then # ----
import re
matches = list(re.finditer(r'"""\n\n# ---- CloudData', content[adm_content_start:]))
for m in matches:
    print(f'Match at {m.start()+adm_content_start}: {repr(m.group())}')
