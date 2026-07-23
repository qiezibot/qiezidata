import urllib.request, ssl, http.cookiejar, json, sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
handler = urllib.request.HTTPSHandler(context=ctx)
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), handler)

# 1. Debug endpoint
r = opener.open('https://qiezidata-production.up.railway.app/debug', timeout=30)
debug_data = json.loads(r.read())
print('=== /DEBUG ===')
print(json.dumps(debug_data, indent=2, ensure_ascii=False))

# 2. Login as admin
data = b'username=admin&password=admin123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
r = opener.open(req, timeout=30)
print(f'\n=== Admin login: status={r.status}, url={r.url} ===')

# Check home page content
r2 = opener.open('https://qiezidata-production.up.railway.app/', timeout=30)
body = r2.read().decode('utf-8')
print(f'Admin page has \u4eea\u8868\u76d8 (\u4eea\u8868\u76d8): {"仪表盘" in body}')
print(f'Admin page has \u7528\u6237\u7ba1\u7406: {"用户管理" in body}')
print(f'Admin page has \u9000\u51fa\u767b\u5f55: {"退出登录" in body}')

# Test /me
r3 = opener.open('https://qiezidata-production.up.railway.app/me', timeout=30)
print(f'/me: {r3.read().decode("utf-8")}')

# Test admin endpoints
try:
    r4 = opener.open('https://qiezidata-production.up.railway.app/admin/users', timeout=10)
    users = json.loads(r4.read())
    print(f'/admin/users: {r4.status}, count={len(users)}')
    for u in users:
        print(f'  id={u.get("id")}, username={u.get("username")}, role={u.get("role")}')
except Exception as e:
    print(f'/admin/users: {e}')

# Now logout and test as qiezi (known password: qiezi123)
cj2 = http.cookiejar.CookieJar()
opener2 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj2), handler)

data = b'username=qiezi&password=qiezi123'
req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
try:
    r = opener2.open(req, timeout=30)
    print(f'\n=== Qiezi login: status={r.status}, url={r.url} ===')
    r2 = opener2.open('https://qiezidata-production.up.railway.app/', timeout=30)
    body = r2.read().decode('utf-8')
    print(f'Qiezi page has 仪表盘: {"仪表盘" in body}')
    print(f'Qiezi page has 用户管理: {"用户管理" in body}')
    print(f'Qiezi page has 退出登录: {"退出登录" in body}')
    r3 = opener2.open('https://qiezidata-production.up.railway.app/me', timeout=10)
    print(f'/me: {r3.read().decode("utf-8")}')
except Exception as e:
    print(f'\nQiezi login error: {e}')

# Test as chengzi - try common passwords
for pw in ['chengzi123', 'chengzi', 'test1234', '123456', 'qiezi123']:
    cj3 = http.cookiejar.CookieJar()
    opener3 = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj3), handler)
    data = f'username=chengzi&password={pw}'.encode()
    req = urllib.request.Request('https://qiezidata-production.up.railway.app/login', data=data, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        r = opener3.open(req, timeout=10)
        if r.url and r.url != '/login':
            print(f'\n=== Chengzi login SUCCESS with password: {pw} ===')
            r2 = opener3.open('https://qiezidata-production.up.railway.app/', timeout=10)
            body = r2.read().decode('utf-8')
            print(f'Chengzi page has 仪表盘: {"仪表盘" in body}')
            print(f'Chengzi page has 用户管理: {"用户管理" in body}')
            print(f'Chengzi page has 退出登录: {"退出登录" in body}')
            r3 = opener3.open('https://qiezidata-production.up.railway.app/me', timeout=10)
            print(f'/me: {r3.read().decode("utf-8")}')
            break
    except:
        pass
else:
    print('\n=== Chengzi: none of the guessed passwords worked ===')
