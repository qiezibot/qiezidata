import sys, requests
sys.stdout.reconfigure(encoding='utf-8')
base = 'https://qiezidata-production.up.railway.app'

# Admin test
s = requests.Session()
r = s.post(f'{base}/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)
r2 = s.get(f'{base}/?t=1', timeout=10)
print(f'=== admin login: {r.status_code} -> home: {r2.status_code} ===')
print(f'Page len: {len(r2.text)}')
print(f'Has 用户管理: {"用户管理" in r2.text}')
print(f'Has 仪表盘: {"仪表盘" in r2.text}')
print(f'Has 上传: {"上传" in r2.text}')

# Non-admin test (qiezi)
s2 = requests.Session()
r = s2.post(f'{base}/login', data={'username':'qiezi','password':'qiezi123'}, allow_redirects=False)
r2 = s2.get(f'{base}/?t=2', timeout=10)
print(f'\n=== qiezi (non-admin) login: {r.status_code} -> home: {r2.status_code} ===')
print(f'Page len: {len(r2.text)}')
print(f'Has 用户管理: {"用户管理" in r2.text}')
print(f'Has 仪表盘: {"仪表盘" in r2.text}')
print(f'Has 上传: {"上传" in r2.text}')
print(f'Has 云数据: {"云数据" in r2.text or "clouddata" in r2.text}')
