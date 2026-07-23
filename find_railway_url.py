import sys, json, base64, re

d = json.load(sys.stdin)
content = base64.b64decode(d['content']).decode()

urls = re.findall(r'(?:https?://[^\s\"\'<>]+)', content)
for u in urls:
    if 'railway' in u or 'up.railway' in u:
        print(u)
