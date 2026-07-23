import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)

# Try direct SQL execution if the endpoint exists
r = s.get('https://qiezidata-production.up.railway.app/admin/exec_sql', params={'sql': "UPDATE users SET id=1 WHERE id=4"})
print(f'SQL exec: {r.status_code} {r.text[:200]}')

# If not, try via the API - delete user id=4 but need to create new admin first
# Actually just patch the user_roles table
print()
print('Current users:')
r = s.get('https://qiezidata-production.up.railway.app/admin/users')
users = r.json()
for u in users:
    print(f'  id={u["id"]}: {u["username"]} role={u["role"]}')
