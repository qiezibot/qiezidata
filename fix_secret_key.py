"""设置 Railway 的 SECRET_KEY 环境变量，避免容器重启后登录失效"""
import requests, base64, json

token = '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'
railway_token = 'HtDR2fKWVj3NXxpnxWF9lWxVmNYoA1FTBdRs1G5iPkjNQ6UfJLp2h6Dgg3rfgE6a'

# Railway API - 设置项目变量
# Railway 的 REST API: https://api.railway.app/graphql/v2
# 或者通过 Railway CLI

# 先用 GitHub API 在代码里加个后备方案
# 让代码自动把 SECRET_KEY 存到文件

github_headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=github_headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')
sha = r.json()['sha']

# 修改 SECRET_KEY 逻辑：第一次生成后存到文件，后续读取
old = '''SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))'''
new = '''# 持久化 SECRET_KEY，避免容器重启后登录失效
_SECRET_FILE = 'secret_key.txt'
def _get_secret():
    try:
        import os
        sk = os.environ.get('SECRET_KEY')
        if sk: return sk
        if os.path.exists(_SECRET_FILE):
            with open(_SECRET_FILE) as f: return f.read().strip()
    except: pass
    sk = secrets.token_hex(32)
    try:
        with open(_SECRET_FILE, 'w') as f: f.write(sk)
    except: pass
    return sk
SECRET_KEY = _get_secret()'''

if old in content:
    new_content = content.replace(old, new)
    payload = {
        'message': '持久化 SECRET_KEY，避免容器重启后需重新登录',
        'content': base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
        'sha': sha,
        'branch': 'main'
    }
    r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=github_headers, json=payload)
    print(f'Push: {r2.status_code}')
    if r2.status_code in (200, 201):
        print(f'Commit: {r2.json()["commit"]["sha"][:12]}')
    else:
        print(f'Error: {r2.text[:200]}')
else:
    print('旧代码未找到，先检查内容')
    pos = content.find('SECRET_KEY')
    if pos >= 0:
        print(content[pos:pos+100])
