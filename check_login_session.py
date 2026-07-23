"""检查茄子登录 session 机制"""
import requests, base64, re

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}
r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
content = base64.b64decode(r.json()['content']).decode('utf-8')

m = re.search(r"AUTH_COOKIE\s*=\s*['\"]([^'\"]+)['\"]", content)
if m:
    print('cookie key:', m.group(1))

login_start = content.find('def login')
login_end = content.find('\n\n', login_start)
print('\n--- login ---')
print(content[login_start:login_end][:1500])

auth_start = content.find('def _auth')
auth_end = content.find('\n\n', auth_start)
print('\n--- _auth ---')
print(content[auth_start:auth_end][:500])

logout_start = content.find('def logout')
if logout_start >= 0:
    logout_end = content.find('\n\n', logout_start)
    print('\n--- logout ---')
    print(content[logout_start:logout_end][:500])
