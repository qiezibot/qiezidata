import json, os

path = os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Local State')
with open(path, 'r', encoding='utf-8-sig') as f:
    d = json.load(f)

cache = d.get('profile', {}).get('info_cache', {})
# 找茄子
for k, v in cache.items():
    name = v.get('name', '')
    if '茄' in name or 'qie' in name.lower() or 'eggplant' in name.lower():
        print(f'找到: profile="{k}", name="{name}"')
        print(json.dumps(v, ensure_ascii=False, indent=2))
