import requests as r
base = 'https://qiezidata-production.up.railway.app'
s = r.Session()
s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})

s.post(base + '/clouddata', json={'key': 'export_test1', 'value': 'export test 1'})
s.post(base + '/clouddata', json={'key': 'export_test2', 'value': 'export test 2'})

cd = s.get(base + '/admin/cddata/1?page=1&limit=20&queryType=-1')
print('Items:')
for item in cd.json().get('items', []):
    iid = item['id']
    k = item['k']
    print(f'  [{iid}] k={k}')

exp = s.get(base + '/admin/cddata/export/1/all')
print(f'\nExport status={exp.status_code}')
print(exp.text)

s.delete(base + '/clouddata/export_test1')
s.delete(base + '/clouddata/export_test2')
