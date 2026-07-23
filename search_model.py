"""搜ModelScope上跟修胡子/面部编辑相关的模型"""
from modelscope.hub.api import HubApi
api = HubApi()
result = api.list_models('damo')
if isinstance(result, dict):
    models = result.get('Models', []) or []
else:
    models = result or []
print(f"共{len(models)}个模型")
keywords = ['makeup', 'face', 'skin', 'beard', 'hair', 'edit', 'facial', 'beauty', '美颜', '化妆', '卸妆']
for m in models:
    name = m.get('Name', '') or m.get('name', '')
    cn = m.get('ChineseName', '') or m.get('chinese_name', '') or ''
    tags = name.lower() + cn
    for kw in keywords:
        if kw.lower() in tags:
            print(f"{name} — {cn}")
            break
