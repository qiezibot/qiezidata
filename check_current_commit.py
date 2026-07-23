import requests, json, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current commit SHA
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/branches/main', headers=headers)
commit_sha = r.json()['commit']['sha']
print(f'Current commit: {commit_sha}')

# Get the tree SHA of main
r2 = requests.get(f'https://api.github.com/repos/qiezibot/qiezidata/git/commits/{commit_sha}', headers=headers)
tree_sha = r2.json()['tree']['sha']
print(f'Current tree: {tree_sha}')
