import urllib.request, json, http.cookiejar

API = 'https://qiezidata-production.up.railway.app'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
opener.open(urllib.request.Request(API+'/login', data=b'username=admin&password=admin123', headers={'Content-Type':'application/x-www-form-urlencoded'}))

# Delete old 10 items from project 2
r = opener.open(urllib.request.Request(API+'/admin/cddata/2?page=1&limit=100&queryType=-1'))
data = json.loads(r.read())
for item in data.get('rows', []):
    op = urllib.request.Request(API+f'/admin/cddata/{item["id"]}', method='DELETE')
    opener.open(op)
    print(f"  Deleted: {item['k']}")

# Upload 10 with key=项目名, value=数据内容
project_id = 2
for i in range(1, 11):
    body = json.dumps({'key': f'\u9879\u76ee{i}', 'value': f'\u6570\u636e\u5185\u5bb9{i}', 'project_id': project_id}).encode()
    r = opener.open(urllib.request.Request(API+'/admin/clouddata/add', data=body, headers={'Content-Type':'application/json'}))
    print(f'  \u9879\u76ee{i} -> {r.read().decode()}')
