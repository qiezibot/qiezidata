import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)

for i in range(1, 21):
    u = f'test_user_{i:02d}'
    dn = f'测试用户{i}'
    r = s.post('https://qiezidata-production.up.railway.app/register', data={'username': u, 'display_name': dn, 'password': 'test1234'}, allow_redirects=False)
    print(f'{u}: {r.status_code}')

r = s.get('https://qiezidata-production.up.railway.app/admin/users')
users = r.json()
print(f'\n现在共 {len(users)} 个用户:')
for u in users:
    print(f'  {u["id"]}: {u["username"]} ({u["display_name"]})')
