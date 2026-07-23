import urllib.request, json, http.cookiejar

API = 'https://qiezidata-production.up.railway.app'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
opener.open(urllib.request.Request(API+'/login', data=b'username=admin&password=admin123', headers={'Content-Type':'application/x-www-form-urlencoded'}))

# Upload 10 items to project 2
project_id = 2
for i in range(1, 11):
    body = json.dumps({'key': f'test_data_{i}', 'value': f'这是第{i}条测试数据', 'project_id': project_id}).encode()
    r = opener.open(urllib.request.Request(API+'/admin/clouddata/add', data=body, headers={'Content-Type':'application/json'}))
    print(f'  {i}: test_data_{i} -> {r.read().decode()}')
