import requests
import sys

BASE='https://qiezidata-production.up.railway.app'
for pw in ['qiezi123', 'qiezi', 'test123', '123456', 'admin123', 'qiezidata', 'password']:
    s = requests.Session()
    r = s.post(BASE+'/login', data={'username':'qiezi','password':pw}, allow_redirects=True)
    print(f'pw={pw}: status={r.status_code} url={r.url}')
    text = r.text
    has_users = '用户管理' in text
    has_dash = '仪表盘' in text
    if r.status_code == 200 and '?e=' not in r.url:
        print(f'  SUCCESS! has_users={has_users} has_dash={has_dash}')
        break
