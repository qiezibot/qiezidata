"""Restore d35a9839 and then correctly extract only the modal divs to move them after body"""
import requests, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current version 
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=d35a98399b67', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Extract _ADMIN template
pat = '_ADMIN = """'
adm_start = content.find(pat)
adm_cont = adm_start + len(pat)
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n', adm_cont + 50000)
template = content[adm_cont:adm_end]
print(f'Template: {len(template)} chars')

# Find the 3 modals and extract ONLY their HTML
pmd_pos = template.find('<div id="profileModalDummy"')
pm_pos = template.find('<div id="profileModal"')
pwd_pos = template.find('<div id="pwdModal"')

print(f'Dummy: {pmd_pos}')
print(f'Real: {pm_pos}')
print(f'pwd: {pwd_pos}')

# Each modal's structure: <div id="xxx" style="..."> <div style="..."> ... </div> </div>
# Extract by finding matching </div> for each

def extract_div(text, start):
    """Extract a matching <div> from start position. Returns (extracted, end_pos)."""
    # Count open/close divs
    depth = 0
    pos = start
    for m in re.finditer(r'</?div[^>]*>', text[pos:], re.IGNORECASE):
        tag = m.group()
        tag_pos = pos + m.start()
        if tag.startswith('</div'):
            depth -= 1
            if depth == 0:
                return text[start:tag_pos+6], tag_pos+6
        else:
            depth += 1
    return None, -1

# Extract each modal
dummy_html, dummy_end = extract_div(template, pmd_pos)
real_html, real_end = extract_div(template, pm_pos)
pwd_html, pwd_end = extract_div(template, pwd_pos)

print(f'\nDummy: {len(dummy_html)} chars, ends at {dummy_end}')
print(f'Real: {len(real_html)} chars, ends at {real_end}')
print(f'pwd: {len(pwd_html)} chars, ends at {pwd_end}')

# Remove all 3 modals from their current position and replace with nothing
# They're sequential, so we need to remove from pmd_pos to pwd_end
all_start = pmd_pos  # start of first modal
all_end = pwd_end    # end of last modal

# Remove modals from position
new_template = template[:all_start] + template[all_end:]

# Add modals after <body>
body_pos = new_template.find('<body>')
all_modals = dummy_html + '\n' + real_html + '\n' + pwd_html
new_template = new_template[:body_pos+6] + '\n' + all_modals + '\n' + new_template[body_pos+6:]

print(f'New template: {len(new_template)} chars (was {len(template)})')

# Verify modals are after <body>
new_body = new_template.find('<body>')
for t in ['profileModalDummy', 'profileModal', 'pwdModal']:
    pos = new_template.find(t)
    rel = pos - new_body
    print(f'  {t}: {rel} chars after <body>')

# Rebuild
new_content = content[:adm_cont] + new_template + content[adm_end:]

# Verify Python
try:
    compile(new_content, 'test.py', 'exec')
    print('Python syntax: OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit()

# Get current SHA
curr = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = curr.json()['sha']

# Push
payload = {
    'message': 'Correctly move modals to body top (extract each div individually)',
    'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"][:12]}')
else:
    print(f'Error: {r2.text[:200]}')
