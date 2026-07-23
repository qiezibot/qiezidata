import json, uuid, hashlib, os, time

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Profile 8\Bookmarks')

with open(path, 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

bar = data['roots']['bookmark_bar']
children = bar['children']

# 找最大ID
max_id = 0
for c in children:
    cid = c['id']
    if isinstance(cid, str):
        cid = int(cid)
    if cid > max_id:
        max_id = cid

# 新书签
new_sites = [
    ('七猫作家', 'https://author.qimao.com/'),
    ('起点作家', 'https://write.qidian.com/'),
    ('纵横作家', 'http://author.zongheng.com/'),
    ('飞卢作家', 'https://b.faloo.com/'),
    ('掌阅作家', 'https://author.ireader.com.cn/'),
    ('塔读作家', 'https://author.tadu.com/'),
]

now = int(time.time() * 10000000) + 621355968000000000

for name, url in new_sites:
    max_id += 1
    entry = {
        'date_added': str(now),
        'date_last_used': '0',
        'guid': str(uuid.uuid4()),
        'id': max_id,
        'name': name,
        'type': 'url',
        'url': url
    }
    children.append(entry)

bar['date_modified'] = str(now)

json_str = json.dumps(data, ensure_ascii=False, indent=3)
checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
data['checksum'] = checksum

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=3)

print(f'OK: 已添加{len(new_sites)}个书签到书签栏')
print(f'checksum: {checksum}')
