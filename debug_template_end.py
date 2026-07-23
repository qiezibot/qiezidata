"""Debug template end structure precisely"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

pat = '_ADMIN = """'
adm_start = raw.find(pat)
adm_cont_start = adm_start + len(pat)
adm_end = raw.find('"""\r\n# -*- coding: utf-8 -*-', adm_cont_start)
template = raw[adm_cont_start:adm_end]

# Find last 500 chars precisely
print('TEMPLATE LAST 500 CHARS (raw):')
print(repr(template[-500:]))
print()
print('NL count in last 200:', template[-200:].count('\n'))

# Find all </script> positions in template
positions = []
pos = 0
while True:
    s = template.find('</script>', pos)
    if s < 0: break
    positions.append(s)
    pos = s + 1

print('\nAll </script> positions:')
for p in positions:
    context = template[p:p+100]
    print(f'  {p}: ...{context[:50]}...')

print(f'\nTemplate last-char flags:')
print(f'  Ends with </body>: {template.rstrip().endswith("</body>")}')
print(f'  Last 30 chars (repr): {repr(template[-30:])}')
