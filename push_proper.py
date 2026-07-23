import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

url = 'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py'

# Read the modified file
with open(r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\railway_file_server_modified.py', 'rb') as f:
    new_content = f.read()

content_b64 = base64.b64encode(new_content).decode('utf-8')

# First get the SHA of the OLD file
r = requests.get(url, headers=headers)
old_sha = r.json()['sha']
print(f'Old file SHA: {old_sha}')

# Now push with the new content AND the proper commit structure
# The content API actually does create a commit, but let's check what happened
payload = {
    'message': 'Add change password feature (user + admin) + profile modal',
    'content': content_b64,
    'sha': old_sha,
    'branch': 'main'
}
r2 = requests.put(url, headers=headers, json=payload)
print(f'Status: {r2.status_code}')
if r2.status_code in (200, 201):
    data = r2.json()
    print(f'Commit SHA: {data.get("commit", {}).get("sha", "N/A")}')
else:
    print(json.dumps(r2.json(), indent=2)[:500])
