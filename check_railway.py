import urllib.request, json

# Try to get Railway deploy status - it might have a deployment API
# First check if there's a railway.json or deploy info
TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway.json', headers=headers)
try:
    r = json.loads(urllib.request.urlopen(req).read())
    content = r['content']
    print(base64.b64decode(content).decode())
except Exception as e:
    print(f'No railway.json: {e}')

# Check if there's a deploy key or webhook config
req2 = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/hooks', headers=headers)
r2 = json.loads(urllib.request.urlopen(req2).read())
print(f'\nWebhooks: {len(r2)}')
for h in r2:
    print(f'  {h.get("name","?")} - {h.get("config",{}).get("url","?")[:50]}')
