import requests

# 通过 GitHub API 的 repository_dispatch 来触发
token = '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'
headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'}

# 尝试通过 GitHub 的 deploy 事件触发
# 先看看能不能获取 Railway 的 webhook URL 配置
# 检查仓库的 config
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata', headers=headers)
print('Repo:', r.status_code)
if r.status_code == 200:
    d = r.json()
    print('Default branch:', d.get('default_branch'))

# 尝试用 repository_dispatch 
r2 = requests.post(
    'https://api.github.com/repos/qiezibot/qiezidata/dispatches',
    headers=headers,
    json={'event_type': 'deploy', 'client_payload': {'ref': 'main'}}
)
print('Dispatch:', r2.status_code, r2.text[:200])

# 检查 commit 状态 - push 成功了吗？
r3 = requests.get('https://api.github.com/repos/qiezibot/qiezidata/commits/main', headers=headers)
if r3.status_code == 200:
    sha = r3.json()['sha']
    msg = r3.json()['commit']['message']
    print(f'\nLatest commit: {sha[:12]} - {msg[:60]}')
