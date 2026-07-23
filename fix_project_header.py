import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Fix: the project table header was accidentally changed
# Find the <th>数据名字</th><th>访问Token</th> context - it should be 项目名称
old = '<th>\u6570\u636e\u540d\u79f0</th><th>\u8bbf\u95eeToken</th>'
new = '<th>\u9879\u76ee\u540d\u79f0</th><th>\u8bbf\u95eeToken</th>'

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed project table header: 数据名字 -> 项目名称")
else:
    print("WARNING: project table header not found, checking...")
    # Find all <th>
    idx = content.find('<th>数据名称</th>')
    print(f'数据名称 at {idx}: context={repr(content[max(0,idx-30):idx+50])}')
    idx2 = content.find('<th>数据名字</th>')
    print(f'数据名字 at {idx2}: context={repr(content[max(0,idx2-30):idx2+50])}')

# Also check if the JS column rendering is correct
# The JS used 项目名称 somewhere - let's check all 数据名字
count = content.count('数据名字')
print(f'数据名字 count: {count}')
count2 = content.count('数据名称')
print(f'数据名称 count: {count2}')
count3 = content.count('项目名称')
print(f'项目名称 count: {count3}')

# Verify
idx1 = content.find('"""')
idx2 = content.find('"""', idx1+3) + 3
code = content[idx2:]
compile(code, 'prod', 'exec')
print("Python syntax: VALID")

body = json.dumps({
    "message": "fix: restore project table 项目名称 (was accidentally changed to 数据名字)",
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
