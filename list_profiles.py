import json, os

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Local State')
with open(path, 'r', encoding='utf-8-sig') as f:
    d = json.load(f)

cache = d.get('profile', {}).get('info_cache', {})
print('所有Profile:')
for k, v in cache.items():
    n = v.get('name', '')
    print('  {}: name=【{}】'.format(k, n))

print()
print('Profile目录列表:')
base = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data')
for item in os.listdir(base):
    full = os.path.join(base, item)
    if os.path.isdir(full) and item.startswith('Profile'):
        bm = os.path.join(full, 'Bookmarks')
        exists = '有书签' if os.path.exists(bm) else '无书签'
        print('  {} - {}'.format(item, exists))
