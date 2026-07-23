import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Insert lr example before the closing </div></div>
old_end = '<p style="font-size:13px;color:#999">\u6240\u6709 API \u8bf7\u5728\u6b64\u57fa\u7840\u57df\u540d\u4e0a\u62fc\u63a5\u3002</p>\n</div>\n</div>\n\n<div id="toast" class="toast">'

lr_example = (
    '<p style="font-size:13px;color:#999">\u6240\u6709 API \u8bf7\u5728\u6b64\u57fa\u7840\u57df\u540d\u4e0a\u62fc\u63a5\u3002</p>\n\n'
    '<h4 style="margin:15px 0 5px">\U0001f916 \u61d2\u4eba\u7cbe\u7075\u8c03\u7528\u793a\u4f8b</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>lua</strong> \u83b7\u53d6\u6570\u636e\u5217\u8868\uff08GET\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx&amp;queryType=-1"<br>\n'
    'local resp = http.get(url, {})<br>\n'
    'traceprint(resp.body)<br><br>\n'
    '<strong>lua</strong> \u4e0a\u4f20\u6570\u636e\uff08POST\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx"<br>\n'
    'local body = \'{"key":"test","value":"hello"}\'<br>\n'
    'local headers = {["Content-Type"]="application/json"}<br>\n'
    'local resp = http.post(url, headers, body)<br>'
    'traceprint(resp.body)<br><br>\n'
    '<strong>lua</strong> \u5220\u9664\u6570\u636e\uff08DELETE\uff09<br>\n'
    'local url = "https://qiezidata-production.up.railway.app/api/cddata/123?token=xxx"<br>\n'
    'local resp = http.delete(url, {})<br>'
    'traceprint(resp.body)<br>\n'
    '</div>\n'
    '</div>\n</div>\n\n<div id="toast" class="toast">'
)

if old_end in content:
    content = content.replace(old_end, lr_example, 1)
    print("lr example added OK")
else:
    print("ERROR: old_end not found!")
    idx = content.find('\u6240\u6709 API')
    print(repr(content[idx:idx+400]))
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
    "message": "feat: add lr script example to API docs",
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
