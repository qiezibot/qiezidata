import urllib.request, json, base64, http.cookiejar

# We need to get the actual deployed version's content and patch it
TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}
req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"Current SHA: {sha}")

# Check what's actually in the file for the search placeholder and table header
for phrase in ['\u6570\u636e\u540d\u5b57', '\u6570\u636emarked', '\u8f93\u5165key\u6807\u8bc6\u7b26']:
    idx = content.find(phrase)
    if idx >= 0:
        print(f'Found at {idx}: {repr(content[idx-20:idx+40])}')

# Rename: 输入数据名字搜索数据 -> 输入项目名称搜索数据
old1 = '\u8f93\u5165\u6570\u636e\u540d\u5b57\u641c\u7d22\u6570\u636e'
new1 = '\u8f93\u5165\u9879\u76ee\u540d\u79f0\u641c\u7d22\u6570\u636e'
if old1 in content:
    content = content.replace(old1, new1, 1)
    print('Search placeholder updated: 输入项目名称搜索数据')
else:
    print('WARNING: search placeholder not found')

# Also fix the upload placeholder
old2 = '\u8f93\u5165key\u6807\u8bc6\u7b26'
new2 = '\u8f93\u5165\u9879\u76ee\u540d'
if old2 in content:
    content = content.replace(old2, new2, 1)
    print('Key placeholder updated')
else:
    print('WARNING: key placeholder not found')

# Double check 数据名字
count = content.count('\u6570\u636e\u540d\u5b57')
print(f'Remaining 数据名字 occurrences: {count}')

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
    "message": "fix: replace 输入数据名字搜索数据 + 输入key标识符 with 项目名称",
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
