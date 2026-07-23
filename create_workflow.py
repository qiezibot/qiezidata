import requests, base64

token = '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'
headers = {'Authorization': 'Bearer ' + token}

# 创建 .github/workflows/deploy.yml 来触发 Railway
workflow = '''name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Railway CLI
        run: npm install -g @railway/cli
      - name: Deploy
        run: railway up --service qiezidata
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
'''

b64 = base64.b64encode(workflow.encode()).decode('ascii')

# 先检查 .github/workflows/ 路径
r = requests.get(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/.github',
    headers=headers
)
print('Check .github:', r.status_code)
if r.status_code == 404:
    # 需要先创建目录
    pass

# 创建 workflow 文件
r2 = requests.put(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/.github/workflows/deploy.yml',
    headers=headers,
    json={
        'message': 'add Railway deploy workflow',
        'content': b64
    }
)
print('Create workflow:', r2.status_code)
if r2.status_code in (200, 201):
    print('OK:', r2.json()['content']['sha'][:12])
else:
    print(r2.text[:300])

# 也更新一下 railway.toml 来进一步触发
r3 = requests.get(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway.toml',
    headers=headers
)
if r3.status_code == 200:
    toml_sha = r3.json()['sha']
    toml = '''[build]
builder = "nixpacks"
buildCommand = "pip install -r railway_requirements.txt"

[deploy]
startCommand = "python railway_file_server.py"
'''
    r4 = requests.put(
        'https://api.github.com/repos/qiezibot/qiezidata/contents/railway.toml',
        headers=headers,
        json={
            'message': 'update railway.toml build command',
            'content': base64.b64encode(toml.encode()).decode('ascii'),
            'sha': toml_sha
        }
    )
    print('Update railway.toml:', r4.status_code)
