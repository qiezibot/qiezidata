import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {r['sha']}")

# Find the clouddata table header (not the project table header)
idx = content.find('<th>Id</th>')
if idx >= 0:
    end = content.find('</tr>', idx) + 5
    print(f'Clouddata table header at {idx}: {repr(content[idx:end])}')
    
# Also check all <th> in the document to see if 数据名字 still exists
idx2 = content.find('\u6570\u636e\u540d\u5b57')
if idx2 >= 0:
    print(f'\n"数据名字" found at {idx2}: {repr(content[idx2-20:idx2+40])}')
else:
    print('\n"数据名字" NOT found in file')
