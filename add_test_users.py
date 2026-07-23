import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)

users = [
    ('test_a', '测试A', 'test1234'),
    ('test_b', '测试B', 'test1234'),
    ('test_c', '测试C', 'test1234'),
    ('test_d', '测试D', 'test1234'),
    ('test_e', '测试E', 'test1234'),
]

for u, dn, pw in users:
    r = s.post('https://qiezidata-production.up.railway.app/register', data={'username': u, 'display_name': dn, 'password': pw}, allow_redirects=False)
    print(f'{u}: {r.status_code}')

r = s.get('https://qiezidata-production.up.railway.app/admin/users')
users_data = r.json()
print(f'\n现在共有 {len(users_data)} 个用户:')
for u in users_data:
    print(f'  {u["id"]}: {u["username"]} ({u["display_name"]}) - {u["role"]}')
