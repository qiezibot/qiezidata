import requests as r
base = 'https://qiezidata-production.up.railway.app'
s = r.Session()

# 1. 登录 admin
login = s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'}, allow_redirects=False)
loc = login.headers.get('location', 'no redirect')
print('Login:', login.status_code, '(' + loc + ')')

# 2. 查看 /me
me = s.get(base + '/me')
print('/me:', me.status_code, me.text[:120])

# 3. 管理后台
admin_page = s.get(base + '/')
has_dash = 'Dashboard' in admin_page.text
print('/ (admin):', admin_page.status_code, 'hasDashboard:', has_dash)

# 4. 云数据项目
proj = s.get(base + '/admin/cdprojects')
print('cdprojects:', proj.status_code, proj.text[:120])

# 5. 统计数据
stats = s.get(base + '/admin/cdprojects/stats/1')
print('stats:', stats.status_code, stats.text[:120])

# 6. 云数据列表
cdlist = s.get(base + '/admin/cddata/1')
print('cddata:', cdlist.status_code, cdlist.text[:120])

# 7. 所有用户
users = s.get(base + '/admin/users')
print('users:', users.status_code, users.text[:120])
