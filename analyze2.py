# -*- coding: utf-8 -*-
import sys
c = open(r'C:\Users\lfy20\AppData\Local\Temp\full_utf8.py', 'r', encoding='utf-8').read()

adm = c.find('_ADMIN =')
end_adm = c.find('"""', adm + 10)
adm_content = c[adm:end_adm]

# Save the full admin template for reference
open(r'C:\temp\_ADMIN_HTML.txt', 'w', encoding='utf-8').write(adm_content)

# Print the structure landmarks
print("=== Structure ===")
for keyword in ['page-dashboard', 'page-files', 'page-upload', 'page-users', 'page-clouddata', 'page-apidocs']:
    idx = adm_content.find(keyword)
    print(f"{keyword}: offset {idx}")

# Find all nav items
print("\n=== Nav items ===")
for kw in ['仪表盘', '文件管理', '上传', '用户管理', '云数据', 'API文档']:
    idx = adm_content.find(kw)
    print(f"{kw}: offset {idx}")

# Find all script tags
print("\n=== Script tags ===")
i = 0
while True:
    i = adm_content.find('<script>', i)
    if i < 0: break
    j = adm_content.find('</script>', i)
    print(f"  <script> at {i}, </script> at {j}, length {j-i}")
    i = j + 9

# Find the role-indicator div
ri = adm_content.find('role-indicator')
print(f"\nrole-indicator at: {ri}")
print(adm_content[ri:ri+200])

print("\n=== Done ===")
print(f"Total _ADMIN length: {len(adm_content)}")
