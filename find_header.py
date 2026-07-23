import sys, json, base64

d = json.load(sys.stdin)
content = base64.b64decode(d['content']).decode()

idx = content.find('\u9000\u51fa')
print(f'logout at: {idx}')
s = content[idx-100:idx+200]
# escape non-ASCII
escaped = s.encode('unicode_escape').decode('ascii')
print(escaped)
