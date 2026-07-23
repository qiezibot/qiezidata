import sys, re
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()

# _ADMIN 确切边界
# 从 38235 (""" 起始) 到 68089 (""" 结束)
ADMIN_START = 38235 + 3  # skip """
ADMIN_END = 68089  # position of """ that ends _ADMIN

html = c[ADMIN_START:ADMIN_END]
print(f'ADMIN range: {ADMIN_START}-{ADMIN_END}, {len(html)} chars')
print(f'Ends with: {repr(html[-50:])}')
print(f'Has filter/delete/edit row: {"role===" in html}')
