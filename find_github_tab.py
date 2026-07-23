import sys, re, json
text = sys.stdin.read()
tabs = json.loads(text)
for t in tabs:
    url = t.get('url', '')
    if 'github.com' in url:
        print(t['id'], url)
