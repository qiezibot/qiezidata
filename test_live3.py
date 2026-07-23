import requests as r, json

base = 'https://qiezidata-production.up.railway.app'
s = r.Session()

# 登录
s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})

# 添加数据后立即查列表
add = s.post(base + '/clouddata', json={'key': 'list_test_1', 'value': 'Check if appears in list'})
print('Add:', add.status_code, add.text[:80])

add2 = s.post(base + '/clouddata', json={'key': 'list_test_2', 'value': 'Second item'})
print('Add2:', add2.status_code, add2.text[:80])

# 查列表
cd = s.get(base + '/admin/cddata/1?page=1&limit=20&queryType=-1')
print('\nFull list:')
if cd.status_code == 200:
    d = cd.json()
    print(f'Total: {d.get("total")}, Items: {len(d.get("items",[]))}')
    for item in d.get('items',[]):
        print(f'  [{item["id"]}] k={item["k"]}, t={item.get("t","")}, read={item.get("read")}')

# 搜索测试（搜索 name 字段）
sr = s.get(base + '/admin/cddata/1?page=1&limit=20&queryType=-1&search=list_test_1')
print('\nSearch "list_test_1":')
print(f'  Status: {sr.status_code}')
if sr.status_code == 200:
    print(f'  Total: {sr.json().get("total")}')

# 清理
s.delete(base + '/clouddata/list_test_1')
s.delete(base + '/clouddata/list_test_2')

# 导出测试
exp = s.get(base + '/admin/cddata/export/1/all')
print(f'\nExport all: {exp.status_code} length={len(exp.text)}')
print(exp.text[:200])
