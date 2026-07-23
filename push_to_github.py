import requests, base64, json

token = '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'
url = 'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current file SHA
r = requests.get(url, headers=headers)
data = r.json()
sha = data['sha']
print(f'Current SHA: {sha}')

# Read modified file
with open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'rb') as f:
    new_content = f.read()

# Encode to base64
content_b64 = base64.b64encode(new_content).decode('utf-8')

# Push
payload = {
    'message': 'Add change password feature (user + admin) + profile page',
    'content': content_b64,
    'sha': sha,
    'branch': 'main'
}
r2 = requests.put(url, headers=headers, json=payload)
result = r2.json()
if r2.status_code == 200 or r2.status_code == 201:
    new_sha = result['content']['sha']
    print(f'SUCCESS! New SHA: {new_sha}')
else:
    print(f'ERROR {r2.status_code}: {result.get("message", "")}')
    print(json.dumps(result, indent=2)[:500])
