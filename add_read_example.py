import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Insert read data example after the GET list example, before POST example
old_lr = ('<strong>lua</strong> \u4e0a\u4f20\u6570\u636e\uff08POST\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx"<br>\n'
    'local body = \'{"key":"test","value":"hello"}\'<br>\n'
    'local headers = {["Content-Type"]="application/json"}<br>\n'
    'local resp = http.post(url, headers, body)<br>'
    'traceprint(resp.body)')

new_lr = ('<strong>lua</strong> \u4e0a\u4f20\u6570\u636e\uff08POST\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx"<br>\n'
    'local body = \'{"key":"test","value":"hello"}\'<br>\n'
    'local headers = {["Content-Type"]="application/json"}<br>\n'
    'local resp = http.post(url, headers, body)<br>'
    'traceprint(resp.body)<br><br>\n'
    '<strong>lua</strong> \u83b7\u53d6\u5355\u6761\u6570\u636e\uff08GET\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/{data_id}?token=xxx"<br>\n'
    'local resp = http.get(url, {})<br>'
    'traceprint(resp.body)')

if old_lr in content:
    content = content.replace(old_lr, new_lr, 1)
    print("read data example added OK")
else:
    print("ERROR: old_lr not found!")
    idx = content.find('\u4e0a\u4f20\u6570\u636e\uff08POST\uff09')
    if idx >= 0:
        print(repr(content[idx:idx+300]))
    exit(1)

# Verify
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
try:
    compile(code, 'prod', 'exec')
    print("Python syntax: VALID")
except SyntaxError as e:
    print(f"ERROR line {e.lineno}: {e.msg}")
    exit(1)

body = json.dumps({
    "message": "feat: add get single data lua example to API docs",
    "content": base64.b64encode(content.encode('utf-8')).decode(),
    "sha": sha,
}).encode()

put_req = urllib.request.Request(
    "https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py",
    data=body, method="PUT",
    headers={**headers, "Content-Type": "application/json"}
)
put_r = urllib.request.urlopen(put_req)
resp = json.loads(put_r.read())
print(f"Push OK, new SHA: {resp['content']['sha']}")
