"""Move profileModal, pwdModal, and profileModalDummy to just after <body> in the admin template"""
import requests, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# Extract _ADMIN template
pat = '_ADMIN = """'
adm_start = content.find(pat)
adm_cont = adm_start + len(pat)
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n', adm_cont + 50000)
template = content[adm_cont:adm_end]
print(f'Template: {len(template)} chars')

# Find all 3 modals' positions
pmd_start = template.find('profileModalDummy')
pm_start = template.find('<div id="profileModal"')
pwd_start = template.find('<div id="pwdModal"')

print(f'profileModalDummy: {pmd_start}')
print(f'profileModal: {pm_start}')
print(f'pwdModal: {pwd_start}')

# Find the closing </div> for each modal (they all share the same </div>\n</div> end)
# The last modal ends just before </body>
# Find where the last modal's closing div is
last_modal_end = template.rfind('</div>')
if template[last_modal_end:last_modal_end+7] == '</div>\n':
    last_modal_end += 7  # include the newline
print(f'Last modal closing div at {last_modal_end}')

# Now find what's right before the first modal (profileModalDummy)
# It's probably inside a card or tab-page content
before_first_modal = template[max(0,pmd_start-300):pmd_start]
print(f'\nContent before profileModalDummy:')
print(before_first_modal)

# Strategy: extract all the modal HTML and move it to after <body>
# Find the true container that wraps all modals
# Looking at the output, modals are inside <div class="card"> in page-apidocs
# I need to find that card's opening tag and remove everything from there to after pwdModal's close

# Find the <div class="card" that's right before profileModalDummy
card_pos = template.rfind('<div class="card"', 0, pmd_start)
print(f'\nCard opening at template: {card_pos}')
if card_pos >= 0:
    card_content = template[card_pos:card_pos+200]
    print(f'Card content: {card_content}')

# Find the <div> that opens the outermost container around all 3 modals
# Start from profileModalDummy and go backward to find the nearest <div
outermost_start = pmd_start
# Count back to see which <div> is the outermost
# Actually, I need to find where the API doc card closes and the modals are inside it
# But they might all be inside one big div that we need to move

# The modals are at the END of the template, after all scripts
# Let me just grab everything from pmd_start to last_modal_end
modal_block = template[pmd_start:last_modal_end]
print(f'\nModal block ({len(modal_block)} chars):')
print(modal_block[:200])
print('...')
print(modal_block[-200:])

# Now find <body> tag
body_pos = template.find('<body>')
print(f'\n<body> at template: {body_pos}')

# Build new template - remove modals from current position, add after <body>
# Remove the modal block from the end
new_template = template[:pmd_start] + template[last_modal_end:]
print(f'Template without modals: {len(new_template)} chars')

# Add modals after <body>
new_template = new_template[:body_pos+6] + '\n' + modal_block + '\n' + new_template[body_pos+6:]
print(f'Final new template: {len(new_template)} chars')

# Verify modals are after <body>
first_pm = new_template.find('profileModal', body_pos)
print(f'First profileModal ref after <body>: at template {first_pm - body_pos} chars after body')

# Rebuild content
new_content = content[:adm_cont] + new_template + content[adm_end:]

# Verify Python syntax
try:
    compile(new_content, 'test.py', 'exec')
    print('Python syntax: OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    exit()

# Verify profileModal count
pm_count = new_content.count('<div id="profileModal"')
pmd_count = new_content.count('<div id="profileModalDummy"')
print(f'profileModal: {pm_count}')
print(f'profileModalDummy: {pmd_count}')
print(f'Size: {len(new_content)} bytes')

# Push
payload = {
    'message': 'Move modal divs (profile, pwd) to body top (outside tab-page)',
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
