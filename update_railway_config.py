import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Check if railway.json exists
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway.json', headers=headers)
if r.status_code == 200:
    sha = r.json()['sha']
    existing = base64.b64decode(r.json()['content']).decode('utf-8')
    print(f'Existing railway.json: {existing}')
    
    # Update watchPatterns
    import json as j
    config = j.loads(existing)
    config['build']['watchPatterns'] = ['railway_file_server.py']
    
    new_content = j.dumps(config, indent=2)
    print(f'New railway.json:')
    print(new_content)
    
    # Push
    payload = {
        'message': 'Add watch pattern to trigger Railway deploy',
        'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
        'sha': sha,
        'branch': 'main'
    }
    r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway.json', headers=headers, json=payload)
    print(f'Push status: {r2.status_code}')
    if r2.status_code in (200, 201):
        print(f'Commit: {r2.json()["commit"]["sha"]}')
    else:
        print(r2.text[:300])
else:
    print(f'railway.json not found: {r.status_code}')
    print(f'Body: {r.text[:200]}')
