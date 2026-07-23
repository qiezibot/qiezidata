import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')

# Find all column header related text near the CD table
for phrase in ['\u6570\u636e\u540d\u5b57', '\u9879\u76ee\u540d\u79f0', '\u6570\u636e', '\u9879\u76ee', 'data名字', 'data\u540d\u5b57', '\u540d\u5b57', '\u6570\u636emarked']:
    idx = content.find(phrase)
    if idx >= 0:
        print(f'Found "{phrase}" at {idx}')
        print(f'  {repr(content[idx-30:idx+50])}')

# Also look in JS code for column rendering
idx_js = content.find('loadCloudDataList')
if idx_js >= 0:
    end = content.find('\n}\n', idx_js)
    if end < 0: end = idx_js + 5000
    # Find the part where columns are rendered
    mid = content[idx_js:end]
    lines = mid.split('\n')
    for i, line in enumerate(lines):
        if any(x in line for x in ['data\u540d\u5b57', '\u6570\u636e\u540d\u5b57', '\u9879\u76ee', '数据', 'name', 'column', 'th>']):
            print(f'  JS line {i}: {line[:120]}')
