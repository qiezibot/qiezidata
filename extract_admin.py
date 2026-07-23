# -*- coding: utf-8 -*-
c = open(r'C:\Users\lfy20\AppData\Local\Temp\full_utf8.py', 'r', encoding='utf-8').read()
adm = c.find('_ADMIN =')
end_adm = c.find('"""', adm + 10)
a = c[adm:end_adm]
out = r'D:\u-claw-backup-20260703\portable\data\.openclaw\workspace\_ADMIN_ref.txt'
open(out, 'w', encoding='utf-8').write(a)
print('wrote', len(a), 'bytes')

# Structure
print('\n=== Structure ===')
for kw in ['page-dashboard', 'page-files', 'page-upload', 'page-users', 'page-clouddata', 'page-apidocs']:
    idx = a.find(kw)
    print(kw, ':', idx)
