import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
c = base64.b64decode(r['content']).decode('utf-8')

idx = c.find('\u8bfb\u53d6\u6570\u636e\u540e\u6807\u4e3a\u5df2\u8bfb')
print(f'Already exists: {idx >= 0}')

idx_del = c.find('\u5220\u9664\u6570\u636e\uff08DELETE\uff09')
print(f'DELETE example at {idx_del}')
print(repr(c[idx_del-60:idx_del+250]))
