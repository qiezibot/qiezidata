import re, base64

c = open('railway_file_server.py', encoding='utf-8').read()

# Find the b64 string
m = re.search(r"base64\.b64decode\('([^']+)'\)", c)
if m:
    raw = base64.b64decode(m.group(1))
    content = raw.decode('utf-8')
    print(f'Decoded: {len(content)} chars')
    print('Has openProfile:', 'openProfile' in content)
    print('Has submitAdmin:', 'submitAdmin' in content)
    print('First 100:', content[:100])
    print('Last 100:', content[-100:])
else:
    print('base64 string not found')
    # Try double-quote version
    m = re.search(r'base64\.b64decode\(\\"([^\\"]+)\\"\)', c)
    if m:
        print('Found with escaped quotes')
