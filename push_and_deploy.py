import requests, base64
GH_TOKEN = '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'

# Get current file from GitHub main branch  
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=main',
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Accept': 'application/vnd.github.v3+json'})
data = r.json()
sha = data['sha']
print('Current SHA:', sha[:10])

# Read local, encode, push
content = open('railway_file_server.py', 'r', encoding='utf-8').read()
encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

r = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Accept': 'application/vnd.github.v3+json'},
    json={'message': 'redeploy', 'content': encoded, 'sha': sha, 'branch': 'main'})
print('Status:', r.status_code)
if r.status_code in (200, 201):
    print('New SHA:', r.json()['content']['sha'][:10])
else:
    print('Error:', r.text[:200])
