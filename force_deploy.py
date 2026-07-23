import requests, json

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

# Get current commit SHA for refs/heads/main
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/branches/main', headers=headers)
current_commit = r.json()['commit']['sha']
print(f'Current ref commit: {current_commit}')

# Create an empty commit via Git Data API to force a new commit
# First get latest tree
r2 = requests.get(f'https://api.github.com/repos/qiezibot/qiezidata/git/commits/{current_commit}', headers=headers)
tree_sha = r2.json()['tree']['sha']
print(f'Tree SHA: {tree_sha}')

# Create new commit with same tree (empty commit)
r3 = requests.post('https://api.github.com/repos/qiezibot/qiezidata/git/commits', headers=headers, json={
    'message': 'Trigger Railway deploy',
    'tree': tree_sha,
    'parents': [current_commit]
})
if r3.status_code in (200, 201):
    new_commit = r3.json()['sha']
    print(f'New commit created: {new_commit}')
    
    # Update ref
    r4 = requests.patch('https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main', headers=headers, json={
        'sha': new_commit,
        'force': False
    })
    print(f'Ref update: {r4.status_code}')
    if r4.status_code == 200:
        print(f'Updated to: {r4.json()["object"]["sha"]}')
    else:
        print(r4.text[:200])
else:
    print(f'Commit create failed: {r3.status_code} {r3.text[:200]}')
