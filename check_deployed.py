import urllib.request, json, http.cookiejar, base64

# Get the last SUCCESSFULLY deployed version from Railway
# The active deployment is "feat: add /api/cddata/{project_id}/fetchone..."
# Let's find that commit SHA
TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

# Find the commit "feat: add /api/cddata/{project_id}/fetchone..."
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/commits?per_page=10', headers=headers)
commits = json.loads(urllib.request.urlopen(req).read())
for c in commits:
    msg = c['commit']['message']
    if 'fetchone' in msg or 'rename 数据名字' in msg or 'replace all 数据名字' in msg or 'column header' in msg:
        print(f"{c['sha'][:10]} - {msg[:60]}")

# The successful deploy is a92ecd45 (fetchone)
# Let's get that file content
sha = 'a92ecd45c89af80ae9bda7a0ae27aab8ed33c6d8'
req2 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/trees/{sha}', headers=headers)
tree = json.loads(urllib.request.urlopen(req2).read())
print(f'\nTree type: {tree.get("type")}')

# Get the actual content via the commit
req3 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/commits/{sha}', headers=headers)
commit_info = json.loads(urllib.request.urlopen(req3).read())
tree_sha = commit_info['commit']['tree']['sha']
print(f'Tree SHA: {tree_sha}')

# Get tree entries
req4 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/trees/{tree_sha}', headers=headers)
tree2 = json.loads(urllib.request.urlopen(req4).read())
for entry in tree2['tree']:
    if entry['path'] == 'railway_file_server.py':
        print(f'Blob SHA: {entry["sha"]}')
        req5 = urllib.request.Request(f'https://api.github.com/repos/qiezibot/qiezidata/git/blobs/{entry["sha"]}', headers=headers)
        blob = json.loads(urllib.request.urlopen(req5).read())
        content = base64.b64decode(blob['content']).decode('utf-8')
        
        # Find all occurrences of 数据名字
        count = content.count('数据名字')
        print(f'数据名字 in a92ecd45: {count}')
        
        # Find the search placeholder
        idx = content.find('搜索数据')
        if idx >= 0:
            print(f'Search placeholder: {repr(content[idx-30:idx+20])}')
        
        idx2 = content.find('<th>Id</th>')
        if idx2 >= 0:
            end = content.find('</tr>', idx2) + 5
            print(f'Table header: {content[idx2:end]}')
        break
