import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')

# Search for /api/ in route decorators specifically
import re
for m in re.finditer(r"@app\.(get|post|delete|put)\('([^']+)'\)", content):
    route = m.group(2)
    if 'api' in route and 'admin' not in route:
        print(f"Found: @app.{m.group(1)}('{route}')")
        # Show body
        end = m.end()
        body_end = content.find('\n\n', end)
        if body_end < 0:
            body_end = end + 300
        print(f"Body: {repr(content[m.start():body_end+1][:300])}")
        print('---')

# Also check for /api/ without /admin/
print("\n=== Search /api/cddata ===")
idx = content.find('/api/cddata')
while idx >= 0:
    line_start = content.rfind('\n', 0, idx) + 1
    line_end = content.find('\n', idx)
    print(f"Line: {content[line_start:line_end]}")
    idx = content.find('/api/cddata', line_end)
