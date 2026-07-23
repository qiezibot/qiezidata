"""Move profileModal and pwdModal to the very top of the page body
so they're not affected by any tab-page display:none CSS inheritance.
Also ensure the inner content container has explicit display:block.
"""
import requests, json, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Find profileModalDummy (the first one)
dummy_start = content.find('<div id="profileModalDummy"')
dummy_end = content.find('</div>\n</div>\n</body>', dummy_start)

# Find real profileModal (the second one)
real_start = content.find('<div id="profileModal"')
real_end = content.find('</div>\n</div>\n</body>', real_start)

# Find pwdModal (different div)
pwd_start = content.find('<div id="pwdModal"')
pwd_end = content.find('</div>\n</div>\n</body>', pwd_start)

print(f'Dummy: {dummy_start}-{dummy_end}')
print(f'Real: {real_start}-{real_end}')
print(f'pwdModal: {pwd_start}-{pwd_end}')

# Verify these are the closing divs before </body>
body_end = content.rfind('</body>')
print(f'</body> at {body_end}')

# The structure should be:
# ... </div>\n</div>\n</div>\n</body>
# dummy:   </div>\n</div> closes the inner and outer
# then </div>\n</div> for pwdModal inner and outer
# then </body>

# Better approach: extract all three modals and move them together right after <body>
# Find where body starts
body_tag = content.find('<body>')
if body_tag < 0:
    body_tag = content.find('<body')

# Find content between all scripts and modals (everything from above body to end)
# Actually let me find the position of the first div after the last script
script_end = content.rfind('</script>') + 9

# Content from script_end to </body> (should be profileModalDummy + profileModal + pwdModal)
footer_content = content[script_end:-7]  # remove \n</body>
print(f'\nFooter content ({len(footer_content)} bytes):')
print(footer_content[:100])
print('...')
print(footer_content[-100:])

# Now move all modals to after <body>
new_content = content[:body_tag+6] + '\n' + footer_content + '\n' + content[body_tag+6:script_end] + '\n</body>'

new_len = len(new_content)
old_len = len(content)
print(f'\nSize: {old_len} -> {new_len}')
print(f'Change: {new_len - old_len}')

# Check profileModal positions in new content
pm_count = len([m.start() for m in re.finditer('<div id="profileModal"', new_content)])
pmd_count = new_content.count('profileModalDummy')
print(f'profileModal divs: {pm_count}')
print(f'profileModalDummy: {pmd_count}')

# Push
payload = {
    'message': 'Move modals (profile+pwd) to top of body, away from tab-page CSS influence',
    'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
else:
    print(r2.text[:300])
