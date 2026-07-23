import json, hashlib, os, time, uuid

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Profile 8\Bookmarks')

with open(path, 'rb') as f:
    raw = f.read()

data = json.loads(raw.decode('utf-8-sig'))

bar = data['roots']['bookmark_bar']
children = bar['children']

# 删除之前添加的重复/错误的小说书签（名字包含"作家"、"小说"、"七猫"、"起点"、"纵横"、"飞卢"、"掌阅"、"塔读"、"作者"的书签）
new_children = []
removed_count = 0
for c in children:
    n = c.get('name', '')
    # 保留原来的番茄小说（id=20，url是fanqienovel.com的那个）
    if c.get('id') == 20 and '作家' in n and '番茄' in n:
        new_children.append(c)
        continue
    # 检查是不是我们之前加的
    keywords = ['七猫', '起点', '纵横', '飞卢', '掌阅', '塔读', '作者专区']
    skip = False
    for kw in keywords:
        if kw in n:
            skip = True
            removed_count += 1
            break
    if not skip:
        new_children.append(c)

print('删除了 %d 条重复书签' % removed_count)
print('剩余 %d 条' % len(new_children))

# 找最大ID
max_id = 0
for c in new_children:
    cid = c['id']
    if isinstance(cid, str):
        cid = int(cid)
    if cid > max_id:
        max_id = cid

# 新书签 - 干净版本
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
    new_children.append(entry)

bar['children'] = new_children
bar['date_modified'] = str(now)

json_str = json.dumps(data, ensure_ascii=False, indent=2)
checksum = hashlib.md5(json_str.encode('utf-8')).hexdigest()
data['checksum'] = checksum

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('OK: 已添加%d个小说平台书签（干净版本，id连续）' % len(new_sites))
print('checksum:', checksum)

# 验证
print('\n验证书签栏:')
for c in data['roots']['bookmark_bar']['children']:
    print('  id=%s name=%s' % (c['id'], c['name']))
