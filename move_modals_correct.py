"""Move modals to right after <body> in the admin template"""
import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
raw = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# Find _ADMIN template boundaries
pat = '_ADMIN = """'
adm_start = raw.find(pat)
adm_cont_start = adm_start + len(pat)
adm_end = raw.find('"""\r\n# -*- coding: utf-8 -*-', adm_cont_start)
template = raw[adm_cont_start:adm_end]
print(f'Template: {len(template)} chars')

# Find <body> and last </script>
body_tag = template.find('<body>')
last_script = template.rfind('</script>') + 9  # past the </script>
print(f'<body> at {body_tag}')
print(f'Last </script> end at {last_script}')

# Content from last_script to end of template (before </body>)
end_content = template.rfind('</body>')
modal_block = template[last_script:end_content]
print(f'Modal block: {len(modal_block)} chars')
print(f'First 100: {modal_block[:100]}')
print(f'Last 100: {modal_block[-100:]}')

# Build new template
part1 = template[:body_tag+6]  # everything up to <body>
part2 = modal_block            # modals moved here
part3 = template[body_tag+6:last_script]  # everything after <body> to last script
part4 = template[end_content:]  # from </body> to end
new_template = part1 + '\n' + part2 + '\n' + part3 + part4

print(f'\nNew template: {len(new_template)} chars')
print(f'Old template: {len(template)} chars')

# Verify profileModal is now after <body>
pm_in_new = new_template.find('profileModal', body_tag)
print(f'profileModal at {pm_in_new - body_tag} chars after <body>')

# Replace in content
new_raw = raw[:adm_cont_start] + new_template + raw[adm_end:]
print(f'\nFinal: {len(new_raw)} bytes')

# Check profileModal count 
pm_count = new_raw.count('<div id="profileModal"')
pmd_count = new_raw.count('profileModalDummy')
print(f'profileModal: {pm_count}, Dummy: {pmd_count}')

# Push
payload = {
    'message': 'Move profile+PWD modals to top of body in admin template',
    'content': base64.b64encode(new_raw.encode('utf-8')).decode('utf-8'),
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code} / {r2.json()["commit"]["sha"][:12]}')
