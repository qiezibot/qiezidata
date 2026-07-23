import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')
print(f"SHA: {r['sha']}")

# Search for all occurrences of 数据名字, 数据name, 项目 etc in the clouddata area
import re
for m in re.finditer(r'[\u4e00-\u9fff]{2,8}', content[40000:]):
    txt = m.group()
    if '名字' in txt or '项目' in txt:
        print(f'  {40000+m.start()}: "{txt}" -> {repr(content[40000+m.start()-10:40000+m.end()+10])}')
