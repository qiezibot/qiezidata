import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)

# Set admin ID to 1
r = s.post('https://qiezidata-production.up.railway.app/admin/user/4/set_id', json={'new_id': 1})
print(f'{r.status_code}: {r.text}')

# Verify
r = s.get('https://qiezidata-production.up.railway.app/admin/users')
users = r.json()
for u in users:
    print(f'  id={u["id"]}: {u["username"]} role={u["role"]}')
