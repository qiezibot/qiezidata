"""Find actual modal positions in the template"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

pat = '_ADMIN = """'
adm_start = raw.find(pat)
adm_cont_start = adm_start + len(pat)
adm_end = raw.find('"""\r\n# -*- coding: utf-8 -*-', adm_cont_start)
template = raw[adm_cont_start:adm_end]

# Find all </script> positions
pos = 0
script_ends = []
while True:
    s = template.find('</script>', pos)
    if s < 0: break
    script_ends.append(s + 9)  # position after </script>
    pos = s + 1

print('Script end positions:', script_ends)

# Find profileModal and pwdModal
pm_start = template.find('<div id="profileModal"')
pmd_start = template.find('<div id="profileModalDummy"')
pwd_start = template.find('<div id="pwdModal"')
body_end = template.find('</body>')

print(f'\nprofileModalDummy: {pmd_start}')
print(f'profileModal: {pm_start}')
print(f'pwdModal: {pwd_start}')
print(f'</body>: {body_end}')

# Which script block is each between?
for se in sorted(script_ends):
    if pmd_start < se:
        print(f'\nDummy is before script ending at {se}')
        break
    if pm_start < se:
        print(f'\nReal is before script ending at {se}')  
        break
    if pwd_start < se:
        print(f'\npwdModal is before script ending at {se}')
        break

# Show content between last script and </body>
last_script_end = script_ends[-1]
between = template[last_script_end:body_end]
print(f'\nBetween last script end ({last_script_end}) and </body>:')
print(repr(between))
print(f'Length: {len(between)} chars')
