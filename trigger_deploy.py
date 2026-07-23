import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

# Get current HEAD
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main', headers=headers)
ref = json.loads(urllib.request.urlopen(req).read())
head_sha = ref['object']['sha']
print(f'HEAD: {head_sha}')

# Get HEAD tree
req2 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/commits/{head_sha}', headers=headers)
commit = json.loads(urllib.request.urlopen(req2).read())
tree_sha = commit['tree']['sha']
print(f'Tree: {tree_sha}, Message: {commit["message"][:50]}')

# Create a new commit with same tree (empty commit to trigger webhook)
new_commit_body = json.dumps({
    "message": "chore: trigger Railway deployment",
    "tree": tree_sha,
    "parents": [head_sha],
}).encode()

req3 = urllib.request.Request(
    'https://api.github.com/repos/qiezibot/qiezidata/git/commits',
    data=new_commit_body, method="POST",
    headers={**headers, "Content-Type": "application/json"}
)
new_commit = json.loads(urllib.request.urlopen(req3).read())
new_sha = new_commit['sha']
print(f'New commit SHA: {new_sha}')

# Update main branch reference
ref_update = json.dumps({
    "sha": new_sha,
    "force": False,
}).encode()

req4 = urllib.request.Request(
    'https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main',
    data=ref_update, method="PATCH",
    headers={**headers, "Content-Type": "application/json"}
)
result = json.loads(urllib.request.urlopen(req4).read())
print(f'Ref updated: {result["ref"]} -> {result["object"]["sha"][:10]}')
