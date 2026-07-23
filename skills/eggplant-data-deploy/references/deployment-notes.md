# 实际部署操作记录（2026-07-21）

本文记录从零搭建茄子数据系统 + 修改权限控制的全过程，作为后续复用的操作手册。

## 一、初始化项目

### 下载代码 → 本地修改 → GitHub推送

```python
import requests, base64

# 从GitHub获取文件
token = 'ghp_xxxx...'
r = requests.get(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': f'token {token}'}
)
sha = r.json()['sha']  # 保存SHA用于后续更新
content = base64.b64decode(r.json()['content']).decode('utf-8')

# 修改内容
content = content.replace('旧文本', '新文本')

# 推回
payload = {
    'message': 'commit message',
    'content': base64.b64encode(content.encode()).decode(),
    'sha': sha,  # 必须传当前SHA，否则409冲突
    'branch': 'main'
}
r2 = requests.put(
    'https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py',
    headers={'Authorization': f'token {token}'},
    json=payload
)
new_sha = r2.json()['content']['sha']
```

### 关键：每次获取文件都要拿新的SHA

```python
# 正确做法：重新GET拿最新SHA再PUT
r = requests.get(url, headers=...)
sha = r.json()['sha']
content = base64.b64decode(r.json()['content']).decode('utf-8')
# 修改后PUT
```

## 二、修改home()让非admin用户也用_ADMIN模板

### 原始代码（问题版本）

```python
async def home(request: Request):
    uid = _auth(request)
    if uid is None: return HTMLResponse(_LOGIN)
    user = await _user(uid)
    if not user: return HTMLResponse(_LOGIN)
    name = user.get('display_name','') or user.get('username','')
    if user.get('role') == 'admin':
        return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', 'admin'))
    return HTMLResponse(_USER.replace('<!--U-->', name))
```

### 修改后（统一模板，role动态注入）

```python
async def home(request: Request):
    uid = _auth(request)
    if uid is None: return HTMLResponse(_LOGIN)
    user = await _user(uid)
    if not user: return HTMLResponse(_LOGIN)
    name = user.get('display_name','') or user.get('username','')
    if user.get('role') == 'admin':
        return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))
    return HTMLResponse(_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', '')))
```

两个 return 都用 `_ADMIN` 模板 + 注入 `<!--U-->` 和 `<!--R-->`。

## 三、JS注入隐藏非admin功能

### 目标

非admin用户看不到"仪表盘"和"用户管理"导航项。

### 注入位置

`_ADMIN` 字符串模板中，最后一个 `</body>` 之前。

### 注入内容

```html
<div id="role-indicator" data-role="<!--R-->" style="display:none"></div>
<script>
(function(){
  var e=document.getElementById("role-indicator");
  var r=e?e.dataset.role:"";
  if(r!="admin"){
    document.querySelectorAll('[onclick*="dashboard"],[onclick*="users"]')
      .forEach(function(n){n.style.display="none"});
  }
})();
</script>
```

### 避坑

Python三引号字符串中，`\"` 的反斜杠会被吃掉！一定要用 `\\"` 或改用单引号外层：

```python
# ❌ 错误：反斜杠被Python吃掉
js = '''...querySelectorAll("[onclick*=\"users\"]")...'''

# ✅ 正确：用单引号包选择器
js = '''...querySelectorAll('[onclick*="users"]')...'''
```

## 四、导航栏logo去链接

```python
# 替换
old = '<a href="/" class="logo">茄子数据</a>'
new = '<span class="logo">茄子数据</span>'
content = content.replace(old, new)
```

## 五、部署验证流程

### 检查部署状态

```python
import requests

# 方式1：看debug端点
r = requests.get('https://yourdomain.up.railway.app/debug')
print(r.json())

# 方式2：admin登录检查模板长度
s = requests.Session()
s.post('https://yourdomain.up.railway.app/login',
       data={'username':'admin','password':'admin123'})
r = s.get('https://yourdomain.up.railway.app/')
print(len(r.text))  # 成功时 > 29000（模板），失败时 = 4467（登录页）

# 方式3：检查JS/内容是否存在
print('role-indicator' in r.text)
```

### 验证权限隐藏

1. 注册新用户（注册后需手动登录）
2. 登录后用snapshot看导航项
3. admin登录确认不受影响

## 六、GitHub API 403处理

GitHub API有时限流（60次/小时未认证）。用token认证后5000次/小时。

```python
headers = {'Authorization': f'token {token}'}
# 或
headers = {'Authorization': f'Bearer {token}'}
```

如果遇到 `404 Not Found`，检查：
1. repo名是否正确
2. token是否过期
3. 文件路径是否正确
