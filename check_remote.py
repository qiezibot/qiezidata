import requests, json, base64

token = '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'
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}

# 检查远程仓库最新 commit
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/commits/main', headers=headers)
print('=== 远程仓库最新 commit ===')
print('Status:', r.status_code)
if r.status_code == 200:
    d = r.json()
    print('SHA:', d['sha'])
    print('Message:', d['commit']['message'])
    print('Date:', d['commit']['committer']['date'])
else:
    print(r.text[:500])

# 查看远程文件大小
r2 = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
print('\n=== 远程 railway_file_server.py ===')
print('Status:', r2.status_code)
if r2.status_code == 200:
    content_b64 = r2.json()['content']
    decoded = base64.b64decode(content_b64).decode('utf-8')
    print('Size:', len(decoded), 'bytes')
    print('Has clouddata_projects:', 'clouddata_projects' in decoded)
    print('Has initCloudData:', 'initCloudData' in decoded)
    print('Has overhaul:', 'overhaul' in decoded)
else:
    print(r2.text[:500])
