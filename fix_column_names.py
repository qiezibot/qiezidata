import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Change table headers
old_th = '<th>\u6570\u636e\u540d\u5b57</th><th>\u6570\u636e</th><th>\u6570\u636eMD5</th>'
new_th = '<th>\u9879\u76ee</th><th>\u6570\u636e</th><th>\u6570\u636eMD5</th>'

if old_th in content:
    content = content.replace(old_th, new_th, 1)
    print("Column headers updated OK")
else:
    print("WARNING: old_th not found!")
    idx = content.find('\u6570\u636e\u540d\u5b57')
    print(repr(content[idx-10:idx+50]))

# Also rename the upload card labels
old_card = '<div style="margin-bottom:8px;font-size:16px;font-weight:bold">\u4e0a\u4f20\u6587\u672c\u6587\u4ef6</div>'
new_card = '<div style="margin-bottom:8px;font-size:16px;font-weight:bold">\u4e0a\u4f20\u6570\u636e</div>'
content = content.replace(old_card, new_card, 1)
print("Card title updated OK")

old_key_label = '<span style="font-size:14px">Key:</span>'
new_key_label = '<span style="font-size:14px">\u9879\u76ee:</span>'
content = content.replace(old_key_label, new_key_label, 1)
print("Key label updated OK")

old_placeholder = 'placeholder="\u8f93\u5165key\u6807\u8bc6\u7b26"'
new_placeholder = 'placeholder="\u8f93\u5165\u9879\u76ee\u540d"'
content = content.replace(old_placeholder, new_placeholder, 1)
print("Placeholder updated OK")

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
    "message": "fix: rename clouddata column headers (name->项目, data->数据) and upload labels",
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
