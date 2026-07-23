import requests, base64, re

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Find _ADMIN triple-quote boundary
pat = '_ADMIN = """'
adm_start = content.find(pat)
adm_cont_start = adm_start + len(pat)
# Find end of template - search for tripe quote ending
# The template ends before the -*- coding line
adm_end = content.find('"""\r\n# -*- coding: utf-8 -*-', adm_cont_start)
if adm_end < 0:
    adm_end = content.find('"""\n# -*- coding', adm_cont_start)

template = content[adm_cont_start:adm_end]
print(f'Template: {len(template)} chars')

# Show last 600 chars
print('LAST 600 OF TEMPLATE:')
print(template[-600:])
print()
print('---')
print('AFTER TEMPLATE:')
after = content[adm_end:adm_end+200]
print(after)
