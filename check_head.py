import urllib.request, json

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

# Get the current HEAD to verify it's the latest
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main', headers=headers)
ref = json.loads(urllib.request.urlopen(req).read())
current_sha = ref['object']['sha']
print(f'Current HEAD SHA: {current_sha}')

# Fetch latest commit message
req2 = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/git/commits/'+current_sha, headers=headers)
commit = json.loads(urllib.request.urlopen(req2).read())
print(f'Latest: {commit["message"][:60]}')
