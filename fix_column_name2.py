import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Find "数据名字" in the JS that loads clouddata rows
old_js_col = "data名字"
new_js_col = "\u9879\u76ee\u540d\u79f0"
content = content.replace(old_js_col, new_js_col, 1)
print("JS column name updated OK")

# Also search for other occurrences of "数据名字"
count = content.count('\u6570\u636e\u540d\u5b57')
if count > 0:
    # Replace remaining
    content = content.replace('\u6570\u636e\u540d\u5b57', '\u9879\u76ee\u540d\u79f0')
    print(f"Replaced {count} more occurrences of \u6570\u636e\u540d\u5b57")

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
    "message": "fix: rename 数据名字 to 项目名称 in clouddata",
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
