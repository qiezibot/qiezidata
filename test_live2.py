import requests as r
import json

base = 'https://qiezidata-production.up.railway.app'
s = r.Session()

# 1. 登录
login = s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'})
print('1. 登录:', login.status_code)

# 2. 测试云数据列表（用正确的 queryType）
print('\n2. 云数据列表 (queryType=-1):')
cd = s.get(base + '/admin/cddata/1?page=1&limit=20&queryType=-1')
print(f'   Status: {cd.status_code}')
if cd.status_code == 200:
    d = cd.json()
    print(f'   Items: {len(d.get("items",[]))}, Total: {d.get("total",0)}')
    for item in d.get('items',[]):
        st = '已读' if item.get('read') else '未读'
        print(f'   [{item["id"]}] key={item["k"]} value={item.get("v","")[:30]} status={st}')
else:
    print(f'   Error: {cd.text[:200]}')

# 3. 添加云数据（用 JSON body）
print('\n3. 云数据添加 (JSON):')
cd_add = s.post(base + '/clouddata', json={'key': 'api_test_key', 'value': 'API test via JSON'})
print(f'   Status: {cd_add.status_code}')
if cd_add.status_code == 200:
    print(f'   OK: {cd_add.text}')
else:
    print(f'   Error: {cd_add.text[:200]}')

# 4. 添加云数据2（用 Form body - 另一种方式）
print('\n4. 云数据添加 (form):')
cd_add2 = s.post(base + '/clouddata', data={'key': 'form_test', 'value': 'Form test value'})
print(f'   Status: {cd_add2.status_code}')

# 5. 查询刚添加的
print('\n5. 查单个:')
cd_get = s.get(base + '/clouddata?key=api_test_key')
print(f'   Status: {cd_get.status_code}')
if cd_get.status_code == 200:
    print(f'   OK: {cd_get.text[:150]}')

# 6. 标记已读
print('\n6. 标记已读:')
cd_mark = s.post(base + '/clouddata/mark/api_test_key?read=true')
print(f'   Status: {cd_mark.status_code} {cd_mark.text[:100]}')

# 7. 搜索
print('\n7. 搜索数据:')
cd_search = s.get(base + '/admin/cddata/1?page=1&limit=20&queryType=-1&search=test')
print(f'   Status: {cd_search.status_code}')
if cd_search.status_code == 200:
    d = cd_search.json()
    print(f'   Found: {d.get("total",0)} items')

# 8. 切换单条状态
print('\n8. 切换状态:')
# 先获取第一条数据
cd_all = s.get(base + '/admin/cddata/1?page=1&limit=1&queryType=-1')
if cd_all.status_code == 200:
    items = cd_all.json().get('items',[])
    if items:
        first_id = items[0]['id']
        toggle = s.post(base + f'/admin/cddata/state/{first_id}')
        print(f'   Toggle {first_id}: {toggle.status_code} {toggle.text[:100]}')

# 9. 项目操作
print('\n9. 项目相关:')
proj = s.get(base + '/admin/cdprojects/stats/1')
print(f'   Stats: {proj.status_code} {proj.text[:100]}')

# 10. 清理测试数据
print('\n10. 删除测试数据:')
cd_del = s.delete(base + '/clouddata/api_test_key')
print(f'   Delete api_test_key: {cd_del.status_code} {cd_del.text[:100]}')
cd_del2 = s.delete(base + '/clouddata/form_test')
print(f'   Delete form_test: {cd_del2.status_code} {cd_del2.text[:100]}')

print('\n========== 测试完成 ==========')
