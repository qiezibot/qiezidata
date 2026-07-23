import urllib.request, ssl, http.cookiejar

ctx = ssl.create_default_context()
handler = urllib.request.HTTPSHandler(context=ctx)

# Use a regular HTTPCookieProcessor to handle redirect + cookie
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), handler)

# 1. Login - let it follow redirect to /
data = b'username=admin&password=admin123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
r = opener.open(req, timeout=30)
# Since login redirects to /, we should now be at /
body = r.read().decode()
print(f'After login: status={r.status}, url={r.url}')
print(f'Contains Dashboard: {"Dashboard" in body}')
print(f'Contains Logout: {"Logout" in body}')

# 2. Cookies should be set by now
print(f'Cookies: {[(c.name, c.value[:20]) for c in cj]}')

# 3. Test /me
r2 = opener.open('https://qiezidata-production.up.railway.app/me', timeout=30)
print(f'/me: {r2.status}, {r2.read().decode()}')

# 4. Test /admin/stats
r3 = opener.open('https://qiezidata-production.up.railway.app/admin/stats', timeout=30)
import json
print(f'/admin/stats: {r3.status}, {json.loads(r3.read())}')

# 5. Test /admin/users
r4 = opener.open('https://qiezidata-production.up.railway.app/admin/users', timeout=30)
users = json.loads(r4.read())
print(f'/admin/users: {r4.status}, users={len(users)}')

# 6. Test /admin/files
r5 = opener.open('https://qiezidata-production.up.railway.app/admin/files', timeout=30)
fjson = json.loads(r5.read())
print(f'/admin/files: {r5.status}, files={len(fjson)}')
