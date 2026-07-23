import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Fix the project table header: 数据名字 -> 项目名称 (in the project table, not CD table)
# The project table header is at: <th>项目ID</th><th>数据名字</th><th>访问Token</th>
old = '<th>\u9879\u76eeID</th><th>\u6570\u636e\u540d\u5b57</th><th>\u8bbf\u95eeToken</th>'
new = '<th>\u9879\u76eeID</th><th>\u9879\u76ee\u540d\u79f0</th><th>\u8bbf\u95eeToken</th>'

content = content.replace(old, new, 1)
print("Fixed project table header")

# Final check
count_cd = content.count('\u6570\u636e\u540d\u5b57')
count_pr = content.count('\u9879\u76ee\u540d\u79f0')
count_name = content.count('\u6570\u636e\u540d\u79f0')
print(f'数据名字: {count_cd} (should be in CD search placeholder)')
print(f'项目名称: {count_pr} (project table)')
print(f'数据名称: {count_name} (CD table header)')

# Find all <th> in document
import re
for m in re.finditer(r'<th>[^<]+</th>', content):
    print(f'  th: {m.group()}')

# Verify
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
compile(code, 'prod', 'exec')
print("Python syntax: VALID")

body = json.dumps({
    "message": "fix: restore project table 项目名称 header",
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
