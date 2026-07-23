import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

# Use the correct API
sha = '9eef26e3772496b44156160dcf4a4ae5af1ee376'

# GET /repos/{owner}/{repo}/git/commits/{sha}
req = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/commits/{sha}', headers=headers)
commit = json.loads(urllib.request.urlopen(req).read())
tree_sha = commit['tree']['sha']
print(f'Tree SHA: {tree_sha}')

req2 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/trees/{tree_sha}', headers=headers)
tree = json.loads(urllib.request.urlopen(req2).read())

for entry in tree['tree']:
    if entry['path'] == 'railway_file_server.py':
        print(f'Blob SHA: {entry["sha"]}')
        req3 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/blobs/{entry["sha"]}', headers=headers)
        blob = json.loads(urllib.request.urlopen(req3).read())
        content = base64.b64decode(blob['content']).decode('utf-8')
        count = content.count('数据名字')
        print(f'数据名字 count in fetchone commit: {count}')
        idx = content.find('数据名字')
        while idx >= 0:
            print(f'  at {idx}: {repr(content[max(0,idx-20):idx+30])}')
            idx = content.find('数据名字', idx + 1)
        break
