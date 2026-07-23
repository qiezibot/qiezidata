import requests, base64, json

token = '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'
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}

# 创建一个 railway.toml 来触发
content = '''[build]
  builder = "nixpacks"
  buildCommand = "pip install -r requirements.txt"

[deploy]
  startCommand = "python railway_file_server.py"
'''

b64 = base64.b64encode(content.encode()).decode('ascii')

# 创建新文件
r = requests.put(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway.toml',
    headers=headers,
    json={
        'message': 'add railway.toml to trigger deploy',
        'content': b64
    }
)
print('Create railway.toml:', r.status_code)
if r.status_code in (200, 201):
    print('OK:', r.json()['content']['sha'][:12])
else:
    print(r.text[:300])
