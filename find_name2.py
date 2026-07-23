import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')
sha = r['sha']
print(f"SHA: {sha}")

# The JS renders x.name in the table. But the column header says "项目".
# Check what the column header is before x.name is rendered
idx = content.find("'+x.name+'")
before = content.rfind('<th', 0, idx)
print(f'Before x.name: {repr(content[before:idx+20])}')

# The issue: column header says "项目" but JS renders x.name (which is the DB field "name")
# Let's see what the full row rendering looks like
start = content.rfind('cdHtml+=', 0, idx)
end = content.find(';', idx)
print(f'\nRow template: {repr(content[start:end+1][:500])}')

# If the header says 项目 but data renders x.name, that's consistent.
# But if there's a "数据名字" somewhere hidden...
# Check all strings near "名字"
for phrase in ['\u540d\u5b57', 'data\u540d', '\u6570\u636e\u540d', 'data名字']:
    i = content.find(phrase)
    if i >= 0:
        print(f'\nFound "{phrase}" at {i}: {repr(content[i-20:i+40])}')
