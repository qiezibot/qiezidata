import requests
BASE='https://qiezidata-production.up.railway.app'

# Check the exact login flow for qiezi
s = requests.Session()
r = s.post(BASE+'/login', data={'username':'qiezi', 'password':'qiezi123'}, allow_redirects=False)
loc = r.headers.get('Location', 'none')
print('qiezi/qiezi123 - status:', r.status_code, 'Location:', loc)

# Check chengzi for comparison
s2 = requests.Session()
r2 = s2.post(BASE+'/login', data={'username':'chengzi', 'password':'chengzi123'}, allow_redirects=False)
loc2 = r2.headers.get('Location', 'none')
print('chengzi/chengzi123 - status:', r2.status_code, 'Location:', loc2)
