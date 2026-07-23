import sys, re
text = sys.stdin.read()
urls = re.findall('"url":\s*"([^"]+)"', text)
for u in urls:
    if not u.startswith('chrome') and not u.startswith('about:'):
        print(u[:120])
