import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
sha = r['sha']
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {sha}")

# Revert: 项目 -> 数据, 项目名称 -> 数据名字 (in the CD table context only)
# But keep: 项目名称 in the project table (that's different table)
# The changes:
# 1. <th>项目</th> -> <th>数据名称</th> (CD table header)
# 2. 选择项目: -> 选择项目: (keep)
# 3. 输入项目名 -> 输入key标识符 (upload key placeholder)
# 4. 输入项目名称搜索数据 -> 输入数据名字搜索数据 (search placeholder)
# 5. 数据（value column header）-> 数据 (keep)
# 6. 项目名称 (search placeholder) -> 数据名字
# 7. JS column: 项目名称 -> 数据名字

changes = [
    # CD table header
    ('<th>项目</th><th>数据</th>', '<th>数据名称</th><th>数据</th>'),
    # Search placeholder
    ('输入项目名称搜索数据', '输入数据名字搜索数据'),
    # Upload key placeholder  
    ('输入项目名', '输入key标识符'),
    # Key label
    ('<span style="font-size:14px">项目:</span>', '<span style="font-size:14px">Key:</span>'),
    # Upload card title
    ('上传数据', '上传文本文件'),
    # JS rendered column - check what the actual JS uses
]

# First check what's actually in the file at key positions
for c in changes:
    ok = c[0] in content
    print(f'  {repr(c[0][:30])}... exists: {ok}')

# The main changes
old1 = '<th>\u9879\u76ee</th><th>\u6570\u636e</th>'
new1 = '<th>\u6570\u636e\u540d\u79f0</th><th>\u6570\u636e</th>'
content = content.replace(old1, new1)
print(f'Table header: 项目 -> 数据名称')

old2 = '\u8f93\u5165\u9879\u76ee\u540d\u79f0\u641c\u7d22\u6570\u636e'
new2 = '\u8f93\u5165\u6570\u636e\u540d\u5b57\u641c\u7d22\u6570\u636e'
content = content.replace(old2, new2)
print(f'Search: 输入项目名称搜索数据 -> 输入数据名字搜索数据')

old3 = '\u8f93\u5165\u9879\u76ee\u540d'
new3 = '\u8f93\u5165key\u6807\u8bc6\u7b26'
content = content.replace(old3, new3)
print(f'Placeholder: 输入项目名 -> 输入key标识符')

old4 = '\u9879\u76ee:'
new4 = 'Key:'
content = content.replace(old4, new4)
print(f'Label: 项目: -> Key:')

# Also fix the JS column name - it was "项目名称" in JS
# Find the JS that renders x.name column
idx = content.find('\u9879\u76ee\u540d\u79f0')
if idx >= 0:
    context = content[max(0,idx-10):idx+15]
    print(f'Found 项目名称 at {idx}: {repr(context)}')
    content = content.replace('\u9879\u76ee\u540d\u79f0', '\u6570\u636e\u540d\u5b57', 1)
    print(f'JS: 项目名称 -> 数据名字')

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
    "message": "fix: revert to 数据名称/数据名字 labels, keep 项目 for project table only",
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
