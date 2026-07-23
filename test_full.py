import requests as r
import json

base = 'https://qiezidata-production.up.railway.app'
s = r.Session()

login = s.post(base + '/login', data={'username': 'admin', 'password': 'admin123'}, allow_redirects=False)
print('=== 1. 登录 ===')
print('Login:', login.status_code, login.headers.get('location',''))

# ===================== 管理后台 =====================
print('\n=== 2. 管理后台 API ===')
me = s.get(base + '/me').json()
print('/me:', json.dumps(me, ensure_ascii=False))

stats = s.get(base + '/admin/stats').json()
print('/admin/stats:', json.dumps(stats, ensure_ascii=False))

users = s.get(base + '/admin/users').json()
print('/admin/users count:', len(users))
for u in users:
    print(f'  [{u["id"]}] {u["username"]} role={u["role"]}')

files = s.get(base + '/admin/files').json()
print('/admin/files count:', len(files))

# ===================== 云数据项目 =====================
print('\n=== 3. 云数据项目 ===')
proj = s.get(base + '/admin/cdprojects').json()
print('Projects:', json.dumps(proj, ensure_ascii=False))

pid = proj[0]['id'] if proj else 1
stats = s.get(base + f'/admin/cdprojects/stats/{pid}').json()
print('Stats:', json.dumps(stats, ensure_ascii=False))

# ===================== 云数据列表 =====================
print('\n=== 4. 云数据列表 ===')
cd = s.get(base + f'/admin/cddata/{pid}?page=1&limit=20&queryType=all').json()
print('Items:', json.dumps(cd, ensure_ascii=False)[:500])

# ===================== 新用户注册 =====================
print('\n=== 5. 注册新用户 ===')
reg_new = s.post(base + '/register', data={'username': 'testuser1', 'password': 'test123', 'display_name': '测试用户1'}, allow_redirects=False)
print('Register testuser1:', reg_new.status_code, reg_new.text[:120])

# ===================== 文件上传测试 =====================
print('\n=== 6. 文件上传 ===')
up = s.post(base + '/upload', files={'file': ('hello.txt', 'Hello World! This is a test file.', 'text/plain')})
print('Upload:', up.status_code, up.text[:200])

myfiles = s.get(base + '/files').json()
print('My files count:', len(myfiles))
if myfiles:
    fid = myfiles[0]['id']
    print(f'First file: {json.dumps(myfiles[0], ensure_ascii=False)[:200]}')

    # 下载
    dl = s.get(base + f'/download/{fid}')
    print(f'Download {fid}: status={dl.status_code} content={dl.text[:100]}')

    # 预览
    rd = s.get(base + f'/read/{fid}')
    print(f'Read {fid}: status={rd.status_code} content={rd.text[:100]}')

    # 删除
    delf = s.delete(base + f'/delete/{fid}')
    print(f'Delete {fid}: {delf.status_code} {delf.text[:100]}')

# ===================== 云数据增删改 =====================
print('\n=== 7. 云数据 CRUD ===')
cd_add = s.post(base + '/clouddata', data={'k': 'test_' + str(r.__version__), 'v': 'API test value'})
print('Add clouddata:', cd_add.status_code, cd_add.text[:100])

cd_get = s.get(base + '/clouddata/test_' + str(r.__version__))
print('Get clouddata:', cd_get.status_code, cd_get.text[:100])

cd_mark = s.post(base + f'/clouddata/mark/test_' + str(r.__version__) + '?read=true')
print('Mark read:', cd_mark.status_code, cd_mark.text[:100])

cd_del = s.delete(base + '/clouddata/test_' + str(r.__version__))
print('Delete clouddata:', cd_del.status_code, cd_del.text[:100])

# ===================== 导出 =====================
print('\n=== 8. 导出 ===')
exp_all = s.get(base + f'/admin/cddata/export/{pid}/all')
print('Export all:', exp_all.status_code, 'length:', len(exp_all.text), exp_all.text[:100])

exp_unread = s.get(base + f'/admin/cddata/export/{pid}/unread')
print('Export unread:', exp_unread.status_code, 'length:', len(exp_unread.text))

# ===================== 批量删除 =====================
print('\n=== 9. 批量删除 ===')
bd = s.delete(base + f'/admin/cddata/batch/{pid}?mode=all')
print('Batch delete (just test the endpoint):', bd.status_code, bd.text[:100])

# ===================== 登出 =====================
print('\n=== 10. 登出 ===')
logout = s.get(base + '/logout', allow_redirects=False)
print('Logout:', logout.status_code, logout.headers.get('location',''))

# 登出后验证不能再访问 /me
me2 = s.get(base + '/me')
print('After logout /me:', me2.status_code, me2.text[:100])

print('\n=========== 全部测试完成 ===========')
