import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')

# Find the routes section more carefully
# Look for @app. in the cddata area
idx = content.find('@app', 64000)
while idx >= 0 and idx < 70000:
    end = content.find('\n', idx)
    line = content[idx:end].strip()
    if 'cddata' in line or 'clouddata' in line:
        # Show this route and its body
        route_end = content.find('\n\n', end)
        if route_end < 0:
            route_end = end + 500
        print(f'Line: {line}')
        print(f'Body: {repr(content[end:route_end+1][:300])}')
        print('---')
    idx = content.find('@app', end)
