import os, base64, json, urllib.request

TOKEN = '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'
REPO = 'qiezibot/qiezidata'
PATH = 'railway_file_server.py'

# Get current SHA
req = urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{PATH}',
    headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/vnd.github.v3+json',
             'User-Agent': 'push-script'})
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print('Current SHA:', data['sha'])

# Read local file
local = open('railway_file_server.py', 'rb').read()
print('Local size:', len(local))
print('Local first 20 bytes:', local[:20].hex())

# Push
body = json.dumps({
    'message': 'update clouddata UI with export/mark buttons',
    'content': base64.b64encode(local).decode(),
    'sha': data['sha'],
}).encode()
put_req = urllib.request.Request(f'https://api.github.com/repos/{REPO}/contents/{PATH}',
    data=body, method='PUT',
    headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json',
             'User-Agent': 'push-script'})
put_r = urllib.request.urlopen(put_req)
resp = json.loads(put_r.read())
print('New SHA:', resp['content']['sha'])
print('Status:', put_r.status)
