import json, os

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Profile 8\Bookmarks')
with open(path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

children = data['roots']['bookmark_bar']['children']
print(f'书签栏共 {len(children)} 条：')
for c in children:
    n = c.get('name', '')
    u = c.get('url', '')
    print(f'  [{n}]  ->  {u}')
