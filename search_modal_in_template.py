"""Find profileModal DIV in the source file with wider search"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

# Find _ADMIN triple-quote boundaries
pat = '_ADMIN = """'
adm_start = raw.find(pat)
adm_cont_start = adm_start + len(pat)

# Try different end patterns
for end_pat in ['"""\r\n#', '"""\n#', '"""\r\n\r\n\r\n\r\n\r\n']:
    end = raw.find(end_pat, adm_cont_start + 10000)
    if end >= 0:
        print(f'End pattern "{end_pat[:10]}..." at {end}')
        break

template = raw[adm_cont_start:end]
print(f'Template from {adm_cont_start} to {end} ({len(template)} chars)')

# Search in template directly
for term in ['profileModal', 'pwdModal', 'modal', 'Dummy']:
    p = template.find(term)
    if p >= 0:
        print(f'\n"{term}" FOUND at template offset {p}!')
        print(template[max(0,p-80):p+200])
    else:
        print(f'"{term}" NOT found in raw template')
        
# Let's just look at the raw source between the quotes
# The real content might have escaped characters
print('\nLast 2000 chars of raw source (template area):')
print(raw[-2000:])
