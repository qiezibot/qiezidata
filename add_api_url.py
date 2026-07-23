import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Find the API docs page and add the API URLs section
# The current doc ends with the Token section
old_ending = '<h4 style="color:#e74c3c">\u83b7\u53d6 Token</h4>\n<p style="font-size:13px;color:#666">\u5728\u4e91\u6570\u636e\u9875\u9762\u521b\u5efa\u9879\u76ee\u540e\uff0c\u9879\u76ee\u8be6\u60c5\u4e2d\u4f1a\u663e\u793a\u5bf9\u5e94\u7684 Token\u3002<br>\nToken \u7528\u4e8e\u9274\u6743\uff0c\u8bf7\u59a5\u5584\u4fdd\u7ba1\u3002</p>'

new_ending = '<h4 style="color:#e74c3c">\u83b7\u53d6 Token</h4>\n<p style="font-size:13px;color:#666">\u5728\u4e91\u6570\u636e\u9875\u9762\u521b\u5efa\u9879\u76ee\u540e\uff0c\u9879\u76ee\u8be6\u60c5\u4e2d\u4f1a\u663e\u793a\u5bf9\u5e94\u7684 Token\u3002<br>\nToken \u7528\u4e8e\u9274\u6743\uff0c\u8bf7\u59a5\u5584\u4fdd\u7ba1\u3002</p>\n\n<h4 style="margin:15px 0 5px">\U0001f517 API \u5730\u5740</h4>\n<p style="font-size:13px;color:#666">\u5f53\u524d\u7ebf\u4e0a\u5730\u5740\uff1a<a href="https://qiezidata-production.up.railway.app" target="_blank">https://qiezidata-production.up.railway.app</a></p>\n<p style="font-size:13px;color:#999">\u6240\u6709 API \u8bf7\u5728\u6b64\u57fa\u7840\u57df\u540d\u4e0a\u62fc\u63a5\u3002</p>'

if old_ending in content:
    content = content.replace(old_ending, new_ending, 1)
    print("API address added OK")
else:
    print("ERROR: old ending not found!")
    idx = content.find('\u83b7\u53d6 Token')
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
    "message": "feat: add API base URL to docs page",
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
