import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

content = content.replace('Key:', '\u6570\u636e\u540d\u79f0:', 1)
print("Key: -> 数据名称:")

content = content.replace('\u8f93\u5165key\u6807\u8bc6\u7b26', '\u8f93\u5165\u6570\u636e\u540d\u79f0', 1)
print("输入key标识符 -> 输入数据名称")

# Verify
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
compile(code, 'prod', 'exec')
print("Python syntax: VALID")

body = json.dumps({
    "message": "fix: upload key label -> 数据名称, placeholder -> 输入数据名称",
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
