import json, hashlib, os, time, uuid

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Profile 8\Bookmarks')

with open(path, 'rb') as f:
    raw = f.read()

data = json.loads(raw.decode('utf-8-sig'))

bar = data['roots']['bookmark_bar']
children = bar['children']

print('书签栏共 %d 条:' % len(children))
for c in children:
    print('  id=%s name=[%s] url=%s' % (c['id'], c['name'], c.get('url','')))
