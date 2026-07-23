"""Search what might disable onclick in the admin template"""
import requests, base64, re

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
content = base64.b64decode(r.json()['content']).decode('utf-8')

# Extract _ADMIN template  
pat = '_ADMIN = """'
adm_start = content.find(pat)
adm_cont_start = adm_start + len(pat)
adm_end = content.find('"""\r\n\r\n\r\n\r\n\r\n', adm_cont_start + 50000)
if adm_end < 0:
    # Try ending at the end of file
    adm_end = content.find('"""', adm_cont_start + 50000)
template = content[adm_cont_start:adm_end]
print(f'Template: {len(template)} chars')

# Search for things that might relate to onclick blocking
terms = ['preventDefault', 'stopP', 'removeAttr', 'propag', 'pointer-events', 'disabled', 'pointerEvents']
for term in terms:
    for m in re.finditer(re.escape(term), template, re.IGNORECASE):
        start = max(0, m.start()-120)
        end = min(len(template), m.end()+120)
        print(f'\n--- "{term}" at offset {m.start()} ---')
        print(template[start:end])

# Check if openProfile is only called from onclick, not via addEventListener anywhere
print('\n=== Checking openProfile references ===')
for m in re.finditer('openProfile', template):
    start = max(0, m.start()-50)
    end = min(len(template), m.end()+50)
    print(f'Offset {m.start()}: ...{template[start:end]}...')
