"""回退到 ac53e86398e0"""
import requests, base64

token = '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'
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json'}

r = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py?ref=ac53e86398e0', headers=headers)
old_content = base64.b64decode(r.json()['content']).decode('utf-8')

curr = requests.get('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
sha = curr.json()['sha']

payload = {
    'message': '回退：移除自动登录修改，保留 modal 修复 + SECRET_KEY'
}
payload['content'] = base64.b64encode(old_content.encode('utf-8')).decode('utf-8')
payload['sha'] = sha
payload['branch'] = 'main'

r2 = requests.put('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers, json=payload)
print(f'Push: {r2.status_code}')
if r2.status_code in (200, 201):
    cid = r2.json()['commit']['sha'][:12]
    print(f'Commit: {cid}')
else:
    print(f'Error: {r2.text[:200]}')
