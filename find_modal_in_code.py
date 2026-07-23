"""Find where modal divs are dynamically added in the code"""
import requests, base64, re

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer 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'})
raw = base64.b64decode(r.json()['content']).decode('utf-8')

# Search for "profileModal" in context that's NOT inside triple quotes
# Search for patterns: ..._ADMIN += ..., ... + _ADMIN + ..., return HTMLResponse(...)
for m in re.finditer(r'profileModal', raw):
    start = max(0, m.start() - 200)
    end = min(len(raw), m.end() + 200)
    snippet = raw[start:end]
    # Is this inside a triple-quoted string?
    triple_before = snippet.count('"""')
    if triple_before % 2 == 1:
        print(f'SKIP (in template) at {m.start()}: {snippet[:100]}')
        continue
    print(f'\nCODE at {m.start()}:')
    print(snippet)
    print()
