import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# 1. Update doc section (API doc header area) - change queryType=-1 to queryType=0 with note
old_doc = '<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=-1<br>\n<span style="color:#999">\u53c2\u6570\uff1aproject_id=\u9879\u76eeID, token=\u9879\u76eeToken, queryType=-1\u5168\u90e8/0\u672a\u8bfb/1\u5df2\u8bfb</span>'
new_doc = '<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=0<br>\n<span style="color:#999">\u53c2\u6570\uff1aproject_id=\u9879\u76eeID, token=\u9879\u76eeToken, queryType=0\u672a\u8bfb/1\u5df2\u8bfb/-1\u5168\u90e8</span>'

if old_doc in content:
    content = content.replace(old_doc, new_doc, 1)
    print("Doc section updated OK")
else:
    print("ERROR: doc section not found!")
    idx = content.find('queryType')
    print(repr(content[max(0,idx-50):idx+200]))
    exit(1)

# 2. Update lua example - change queryType=-1 to queryType=0
old_lua = '<strong>lua</strong> \u83b7\u53d6\u6570\u636e\u5217\u8868\uff08GET\uff09<br>\nlocal url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx&amp;queryType=-1"'
new_lua = '<strong>lua</strong> \u83b7\u53d6\u6570\u636e\u5217\u8868\uff08GET\uff09<br>\nlocal url = "https://qiezidata-production.up.railway.app/api/cddata/2?token=xxx&amp;queryType=0"'

if old_lua in content:
    content = content.replace(old_lua, new_lua, 1)
    print("Lua example updated OK")
else:
    print("ERROR: lua section not found!")
    idx = content.find('\u83b7\u53d6\u6570\u636e\u5217\u8868\uff08GET\uff09')
    print(repr(content[idx-50:idx+200]))
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
    "message": "fix: change default queryType from -1(all) to 0(unread) in API docs",
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
