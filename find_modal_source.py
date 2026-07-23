"""Compare template vs actual HTML to find where modals come from"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

# Search for profileModal and pwdModal in the whole file
for term in ['profileModal', 'pwdModal', 'profileModalDummy']:
    positions = []
    pos = 0
    while True:
        p = raw.find(term, pos)
        if p < 0: break
        positions.append(p)
        pos = p + 1
    print(f'{term}: {len(positions)} occurrences')
    for p in positions[:5]:
        context = raw[max(0,p-50):p+80]
        print(f'  {p}: ...{context}...')

print()
# Check for string concatenation patterns
for term in ['_ADMIN', 'MODAL', '_TEMPLATE']:
    idx = raw.find(term)
    if idx >= 0:
        print(f'{term} at {idx}: {raw[idx:idx+40]}')
