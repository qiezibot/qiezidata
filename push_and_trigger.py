import requests, base64, json

token = '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'
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}

# 读取本地已修复的文件
with open('railway_file_server.py', 'rb') as f:
    content = f.read()

b64content = base64.b64encode(content).decode('ascii')

# 获取 SHA
r = requests.get(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers=headers
)
sha = r.json()['sha']

# 使用 git commit API 创建 commit 确保触发 webhook
# 先获取当前 HEAD tree
r2 = requests.get('https://api.github.com/repos/qiezibot/qiezidata/git/refs/heads/main', headers=headers)
head_sha = r2.json()['object']['sha']

# 通过 Contents API 更新文件（这种方式应该触发 webhook）
payload = {
    'message': 'fix: separate CSS from script tag in admin template',
    'content': b64content,
    'sha': sha
}

r3 = requests.put(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers=headers,
    json=payload
)
print('Update file:', r3.status_code)
if r3.status_code in (200, 201):
    print('Updated SHA:', r3.json()['content']['sha'])
    print('Commit SHA:', r3.json()['commit']['sha'])
else:
    print('Error:', r3.text[:300])
