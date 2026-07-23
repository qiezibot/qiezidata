import requests, json, base64

token = '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'
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}

# 读取本地清理后的文件
with open('railway_file_server.py', 'rb') as f:
    content = f.read()

# 获取当前远端 SHA
r = requests.get(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers=headers
)
sha = r.json()['sha']
print('Remote SHA:', sha)
print('Local size:', len(content), 'bytes')

# 上传新版本
payload = {
    'message': 'fix: PG init_db files table migration bug + fix SQLite clouddata table syntax error',
    'content': base64.b64encode(content).decode('ascii'),
    'sha': sha
}

r2 = requests.put(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers=headers,
    json=payload
)
print('Upload status:', r2.status_code)
if r2.status_code in (200, 201):
    print('Upload OK! New SHA:', r2.json()['content']['sha'])
else:
    print(r2.text[:500])
