import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Replace ALL occurrences of 数据名字 with 项目名称
old = '\u6570\u636e\u540d\u5b57'  # 数据名字
new = '\u9879\u76ee\u540d\u79f0'  # 项目名称

count = content.count(old)
if count > 0:
    content = content.replace(old, new)
    print(f"Replaced {count} occurrences of '数据名字' -> '项目名称'")
else:
    print("WARNING: '数据名字' not found!")
    # search for it anyway
    import re
    for m in re.finditer(r'[\u4e00-\u9fff]{2,8}', content):
        t = m.group()
        if '数据' in t and '名字' not in t and t != '数据MD5' and t != '数据库':
            print(f'  near {m.start()}: {t}')

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
    "message": "fix: replace all 数据名字 with 项目名称",
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
