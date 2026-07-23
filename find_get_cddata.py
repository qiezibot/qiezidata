import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')

# Find the GET /api/cddata/{data_id} route
idx = content.find("@app.get('/api/cddata/{data_id}'")
if idx < 0:
    idx = content.find("@app.get('/api/cddata/")
    if idx < 0:
        idx = content.find('api/cddata/', 60000)  # after route definitions
    
print(f'api/cddata/ at pos {idx}')

# Show 300 chars around it
if idx > 0:
    start = idx - 50
    end = content.find('\n\n', idx)
    if end < 0:
        end = idx + 500
    print(repr(content[start:end+200]))
else:
    # Search broader
    for pat in ['/api/cddata/state', '/api/cddata/', 'cddata']:
        i = content.rfind(pat, 0, 60000)
        j = content.find(pat, 60000)
        print(f'{pat}: last before 60k={i}, first after 60k={j}')
