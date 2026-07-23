import requests, base64, json
GH_TOKEN = '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'

# Read local file
content = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Remove the trigger comment line we added earlier (clean the file)
lines = content.split('\n')
lines = [l for l in lines if '# trigger redeploy' not in l]
clean = '\n'.join(lines)

# Get current SHA from main
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=main', 
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Accept': 'application/vnd.github.v3+json'})
sha = r.json()['sha']

# Push clean version back
encoded = base64.b64encode(clean.encode('utf-8')).decode('utf-8')
r = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': 'Bearer ' + GH_TOKEN, 'Accept': 'application/vnd.github.v3+json'},
    json={'message': 'cleanup trigger + redeploy', 'content': encoded, 'sha': sha, 'branch': 'main'})
print('Status:', r.status_code)
if r.status_code == 200:
    print('New SHA:', r.json()['content']['sha'][:10])
else:
    print('Error:', r.text[:200])
