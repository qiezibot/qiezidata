import re

with open('railway_file_server.py', encoding='utf-8') as f:
    c = f.read()

admin_match = re.search(r'_ADMIN\s*=\s*"""\n(.*?)"""', c, re.DOTALL)
if admin_match:
    html = admin_match.group(1)
    # 找 nav 相关
    for tag in ['nav-item', 'sidebar', '我的文件', 'user-area', 'nav', '<ul>', '<li']:
        idx = html.find(tag)
        if idx > 0:
            print(f'--- Found "{tag}" at {idx} ---')
            print(html[max(0,idx-100):idx+300])
            print('---')
