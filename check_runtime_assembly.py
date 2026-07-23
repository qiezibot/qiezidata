"""Check how _ADMIN is assembled at runtime"""
import requests, base64

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

# Show code around _ADMIN.replace and profileModal assembly
idx = raw.find('_ADMIN.replace')
if idx >= 0:
    print('Context around _ADMIN.replace:')
    # Search backward and forward
    start = max(0, idx - 200)
    end = min(len(raw), idx + 400)
    print(raw[start:end])
    print()

# Also find where profileModal is added to final HTML
for term in ['profileModal', 'pwdModal', 'MODAL', 'modal_html']:
    idx = 0
    while True:
        p = raw.find(term, idx)
        if p < 0: break
        # Only show if it's not inside a triple-quoted string (template)
        before = raw[max(0,p-200):p]
        # Check if it's Python code (not template content)
        if '_ADMIN' not in before and '"""' not in before[-5:]:
            pass
        # Show contexts where it looks like Python code
        if any(x in before for x in ['+=', 'def ', '\ndef', '  ', '    ', 'response']):
            print(f'\n{term} at {p}:')
            start = max(0, p-100)
            end = min(len(raw), p + 150)
            print(raw[start:end])
        idx = p + 1
