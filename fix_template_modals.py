"""Move profileModal and pwdModal to top of body in the template"""
import requests, json, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Find the _ADMIN template via full match
pat = '_ADMIN = """'
adm_start = content.find(pat)
if adm_start < 0:
    print(f'_ADMIN not found, searching...')
    # Try different quote patterns
    for q in ['"""', "'''", '"""']:
        pat = f'_ADMIN = {q}'
        p = content.find(pat)
        if p >= 0:
            print(f'Found at {p} with {q}')
            adm_start = p
            break

adm_content_start = adm_start + len(pat)
# Find matching end - count triple quotes
# Just search for the next triple quote
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n\r\n# ---- CloudData', adm_content_start)
if adm_end < 0:
    adm_end = content.find('"""', adm_content_start + 10000)
    # Verify it's closing the template (follows by newline and code)
    after = content[adm_end+3:adm_end+50]
    print(f'After end quote: {after}')

print(f'_ADMIN at {adm_start}-{adm_end}')
template = content[adm_content_start:adm_end]
print(f'Template: {len(template)} chars')

# Find <body> in template
body_start = template.find('<body>')
print(f'<body> at {body_start} in template')

# Find last </script>
last_script = template.rfind('</script>')
print(f'Last </script> at {last_script} in template')

# Find </body>
body_end_tag = template.find('</body>')
print(f'</body> at {body_end_tag} in template')

# Extract content between last script end and </body>
modal_block = template[last_script+9:body_end_tag]
print(f'Modal block: {len(modal_block)} chars')
print(f'First 100: {modal_block[:100]}')
print(f'Last 100: {modal_block[-100:]}')

# Build new template: body start → modal_block → body content up to last script → ... → </body>
part1 = template[:body_start+6]  # up to and including <body>
part2 = modal_block              # all modals moved here
part3 = template[body_start+6:last_script+9]  # from after <body> to last </script>
part4 = '\n</body>'

new_template = part1 + '\n' + part2 + '\n' + part3 + part4
print(f'New template: {len(new_template)} chars')

# Verify modals come after <body>
pos = new_template.find('<body>')
pm = new_template.find('profileModal', pos)
print(f'First profileModal after <body>: at template char {pm - pos} after body')

# Replace in content
new_content = content[:adm_content_start] + new_template + content[adm_end:]

print(f'\nOld: {len(content)}, New: {len(new_content)}')

# Push
payload = {
    'message': 'Move modals to top of body in HTML template',
    'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    'sha': r.json()['sha'],
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    print(f'Commit: {r2.json()["commit"]["sha"]}')
else:
    print(f'Error: {r2.text[:300]}')
