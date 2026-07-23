---
name: eggplant-data-deploy
description: 云端数据库/文件管理系统搭建——FastAPI + PostgreSQL 多用户后台。含用户注册登录、文件上传管理、云数据API、角色权限控制（admin/user）、修改密码、个人资料。输出单文件Python服务，可部署到Railway/Fly.io。适用场景：小团队文件共享、个人云盘、SaaS后台快速原型、数据管理面板。
---

# 🍆 茄子数据 - 全套部署技能

## 技能概览

搭建一个**多用户文件管理 + 数据存储系统**，全栈单文件 Python 服务：

- 🖥️ 前端：单页应用（CSS + HTML + JS 全部内嵌 `_ADMIN` 模板），管理员后台
- ⚙️ 后端：FastAPI + Uvicorn
- 🗄️ 数据库：SQLite（本地）/ PostgreSQL（生产），自动兼容
- 🚀 部署：Railway / Fly.io
- 📦 源码管理：GitHub

**典型报价**：基础搭建 ¥200-500 | 含定制功能 ¥500-2000 | 含维护 ¥50-200/月

---

## 一、核心文件

项目只有一个文件：**`railway_file_server.py`**（~85KB），包含全部前后端代码。

### 文件结构

```
railway_file_server.py
├── _LOGIN    = """..."""   → 登录/注册页面 HTML
├── _ADMIN    = """..."""   → 管理员后台完整 HTML（含CSS+JS）
├── init_db()               → 建表/迁移逻辑（PG + SQLite双分支）
├── FastAPI 路由
│   ├── GET  /              → home() 渲染后台或登录页
│   ├── GET  /login         → 登录表单提交
│   ├── POST /login         → 验证密码、发cookie
│   ├── GET  /register      → 注册表单
│   ├── POST /register      → 创建用户
│   ├── GET  /logout        → 清除cookie
│   ├── POST /upload        → 文件上传
│   ├── GET  /files         → 文件列表
│   ├── GET  /download/{fid}→ 下载文件
│   ├── DELETE /delete/{fid}→ 删除文件（自己）
│   ├── GET  /me            → 当前用户信息
│   ├── POST /me            → 修改显示名称（✨ 改密码功能）
│   ├── POST /me/change_password          → 自己改密码（✨）
│   ├── POST /admin/user/{uid}/change_password → 管理员改用户密码（✨）
│   ├── GET  /admin/users   → 用户列表（admin only）
│   ├── DELETE /admin/user/{uid} → 删除用户（admin only）
│   ├── GET  /admin/files   → 所有文件（admin only）
│   ├── DELETE /admin/file/{fid} → 删任意文件（admin only）
│   ├── GET  /admin/stats   → 统计（admin only）
│   ├── POST /admin/user/{uid}/set_admin → 设管理员
│   ├── POST /admin/user/{uid}/set_id    → 改用户ID
│   ├── CloudData CRUD      → key-value 数据存储
│   └── GET  /debug         → 调试端点
├── 密码认证
│   ├── _hash(pw)           → 加盐 SHA256
│   ├── _verify(pw, hash)   → 验证
│   ├── _token(uid)         → Cookie token (sha256 + SECRET_KEY)
│   ├── _require(req)       → 从 cookie 解析 uid
│   └── _user(uid)          → 查用户信息
└── main guard:  uvicorn.run(app, host='0.0.0.0', port=port)
```

### 模板变量约定

`_ADMIN` 模板使用两个占位符：

```
<!--U-->  → 用户显示名（登录后右上角显示）
<!--R-->  → 用户角色（admin / user / ''）
```

在 `home()` 中注入：

```python
_ADMIN.replace('<!--U-->', name).replace('<!--R-->', user.get('role', ''))
```

所有用户使用**同一份 HTML**，非 admin 功能的隐藏通过前端 JS 根据 `<!--R-->` 判断。

---

## 二、部署流程

### 1️⃣ 准备代码

```bash
# 创建项目目录
mkdir qiezidata && cd qiezidata
git init
# 从模板复制 railway_file_server.py
# 修改 SECRET_KEY（重要！见下文）
```

### 2️⃣ 固定 SECRET_KEY（否则重启后无法登录）

⚠️ **最重要的坑**：原始代码是 `SECRET_KEY = secrets.token_hex(32)`，每次容器重启生成随机值，所有已登录用户的 cookie token 失效。

**必须改成固定值**：

```python
# 找到这行（约第32行）
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# 改成
SECRET_KEY = os.environ.get('SECRET_KEY', '这里写一个固定随机串')
```

固定随机串可以用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成。

或者用环境变量传入：`SECRET_KEY`（Railway 环境变量中设置）

### 3️⃣ 推送 GitHub

```bash
git add railway_file_server.py
git commit -m "init: 茄子数据后台 v2.1"
git remote add origin https://github.com/你的用户名/qiezidata.git
git push -u origin main
```

### 4️⃣ Railway 部署

1. 打开 [Railway](https://railway.app) → New Project → Deploy from GitHub repo
2. 选择刚才创建的仓库
3. Railway 自动识别 Python 项目
4. **设置环境变量**（Project → Variables）：
   | 变量名 | 值 | 说明 |
   |--------|-----|------|
   | `DATABASE_URL` | *(Raiway 自动生成 PostgreSQL)* | 数据库连接串 |
   | `PORT` | `8080` | 端口（可选） |
   | `UPLOAD_DIR` | `/data/uploads` | 文件上传目录 |
   | `SECRET_KEY` | *(可选的，代码里有默认值)* | 覆盖代码中的固定值 |

5. **Start Command** (Settings → Deploy)：
   ```
   python railway_file_server.py
   ```
6. 部署完成 → Railway 给一个 `xxx.up.railway.app` 域名
7. 可选：绑定自定义域名

### 5️⃣ 验证

访问域名，用 `admin / admin123` 登录。

```python
import requests

# 快速验证
r = requests.get('https://你的域名.up.railway.app/')
assert r.status_code == 200
assert '茄子数据' in r.text

# 登录测试
s = requests.Session()
s.post('https://你的域名.up.railway.app/login',
       data={'username':'admin','password':'admin123'})
r = s.get('https://你的域名.up.railway.app/')
# 登录后模板大小 >> 登录页大小
assert len(r.text) > 20000  # 登录页约4KB，后台约47KB
```

---

## 三、初始化账号

代码自带的 admin 账号在 `init_db()` 中创建：

```python
# admin / admin123
h = _hash('admin123')
conn.execute("INSERT INTO users (...) VALUES (..., 'admin', h, 'Admin', ..., 'admin')")
```

- **用户名：** `admin`
- **密码：** `admin123`
- **角色：** `admin`

可在部署后手动注册其他用户。

---

## 四、核心技术细节

### 4.1 密码系统

```python
# 密码哈希（加盐 SHA256）
def _hash(pw):
    s = secrets.token_hex(16)          # 16字节随机盐
    return s + ':' + hashlib.sha256((s + pw).encode()).hexdigest()

# 验证
def _verify(pw, stored):
    s, h = stored.split(':', 1)
    return h == hashlib.sha256((s + pw).encode()).hexdigest()

# Cookie token（不含敏感信息）
def _token(uid):
    sig = hashlib.sha256(f'{uid}:{SECRET_KEY}'.encode()).hexdigest()[:16]
    return f'{uid}:{sig}'

# 从 cookie 取 uid
def _auth(req):
    raw = req.cookies.get('token', '')
    parts = raw.split(':')
    if len(parts) == 2 and parts[1] == hashlib.sha256(f'{parts[0]}:{SECRET_KEY}'.encode()).hexdigest()[:16]:
        return int(parts[0])
    return None
```

### 4.2 数据库双兼容

自动检测环境，同时支持 SQLite 和 PostgreSQL。

```python
use_pg = bool(DATABASE_URL)  # DATABASE_URL 环境变量存在时用 PG

# 在每条 SQL 中根据 use_pg 选择占位符
row = await db_fetchrow(
    'SELECT * FROM users WHERE id=$1' if use_pg else 'SELECT * FROM users WHERE id=?',
    uid
)
```

| 区别 | PostgreSQL (asyncpg) | SQLite (sqlite3) |
|------|---------------------|-------------------|
| 占位符 | `$1`, `$2`, ... | `?`, `?`, ... |
| 布尔类型 | `BOOLEAN` / `TRUE` / `FALSE` | `INTEGER` / `1` / `0` |
| 自增 | `SERIAL PRIMARY KEY` | `INTEGER PRIMARY KEY AUTOINCREMENT` |
| 时间戳 | `TIMESTAMP DEFAULT NOW()` | `TEXT`（手动 ISO 格式） |
| 查表结构 | `information_schema.columns` | `PRAGMA table_info(table)` |

### 4.3 角色权限控制

**后端**（安全防线）：

```python
# 在需要 admin 权限的路由中
if user.get('role') != 'admin':
    raise HTTPException(status_code=403)
```

**前端**（体验）：

```html
<!-- _ADMIN 模板中注入 -->
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

### 4.4 添加新功能的修改模式

**所有功能都以"手术式修改"方式注入**，不改变单文件结构：

1. **后端路由**：在 `home()` 后面 / 合适位置 `@app.xxx` 插入新函数
2. **HTML 模板**：在 `_ADMIN = """..."""` 字符串中修改
3. **JS 逻辑**：在 `</script>` 前（最后一个 script 标签）插入

---

## 五、常见修改模板

### 5.1 固定 SECRET_KEY

```python
# FROM（原始）
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# TO（生产）
SECRET_KEY = os.environ.get('SECRET_KEY', 'c3adc9837be6a1ad025450a8568e77bb19d3db42221875e2afa7d98c4706af2a')
```

### 5.2 改密码功能（后端 3 路由）

在 `@app.get('/me')` 和下一个 `@app.` 之间插入：

```python
@app.post('/me')
async def update_me(request: Request):
    uid = _require(request)
    data = await request.json()
    dn = data.get('display_name', '')
    if dn:
        if use_pg:
            await db_execute('UPDATE users SET display_name=$1 WHERE id=$2', dn, uid)
        else:
            await db_execute('UPDATE users SET display_name=? WHERE id=?', dn, uid)
    return JSONResponse({'ok': True})

@app.post('/me/change_password')
async def change_my_password(request: Request):
    uid = _require(request)
    data = await request.json()
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    if not new_pw or len(new_pw) < 4:
        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})
    if use_pg:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=$1', uid)
        if not row or row['password_hash'] != _hash(old_pw):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        row = await db_fetchrow('SELECT password_hash FROM users WHERE id=?', uid)
        if not row or row['password_hash'] != _hash(old_pw):
            return JSONResponse({'ok': False, 'detail': '旧密码错误'})
        await db_execute('UPDATE users SET password_hash=? WHERE id=?', _hash(new_pw), uid)
    return JSONResponse({'ok': True})

@app.post('/admin/user/{uid}/change_password')
async def admin_change_user_password(uid: int, request: Request):
    aid = _require(request)
    user = await _user(aid)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403)
    data = await request.json()
    new_pw = data.get('new_password', '')
    if not new_pw or len(new_pw) < 4:
        return JSONResponse({'ok': False, 'detail': '新密码至少4个字符'})
    if use_pg:
        await db_execute('UPDATE users SET password_hash=$1 WHERE id=$2', _hash(new_pw), uid)
    else:
        await db_execute('UPDATE users SET password_hash=? WHERE id=?', _hash(new_pw), uid)
    return JSONResponse({'ok': True})
```

### 5.3 改密码/个人资料（前端JS）

在 `_ADMIN` 模板的最后一个 `</script>` 前插入：

```javascript
function openProfile(){ document.getElementById('profileModal').style.display='flex'; fetch('/me',{credentials:'include'}).then(function(r){return r.json();}).then(function(u){ document.getElementById('profModalUser').value=u.username||''; document.getElementById('profModalDN').value=u.display_name||''; document.getElementById('profModalRole').value=u.role||''; }).catch(function(){}); }
function closeProfile(){ document.getElementById('profileModal').style.display='none'; }
function saveProfileModal(){ var dn=document.getElementById('profModalDN').value.trim(); var msg=document.getElementById('profModalSaveMsg'); msg.style.display='none'; fetch('/me',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({display_name:dn})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='已保存';msg.style.color='#27ae60';}else{msg.textContent=d.detail||'保存失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
function submitProfilePwdModal(){ var oldP=document.getElementById('profModalOldPwd').value; var newP=document.getElementById('profModalNewPwd').value; var newP2=document.getElementById('profModalNewPwd2').value; var msg=document.getElementById('profModalPwdMsg'); msg.style.display='none'; if(!oldP){msg.textContent='请输入旧密码';msg.style.display='block';return;} if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} if(newP!==newP2){msg.textContent='两次输入不一致';msg.style.display='block';return;} fetch('/me/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_password:oldP,new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';document.getElementById('profModalOldPwd').value='';document.getElementById('profModalNewPwd').value='';document.getElementById('profModalNewPwd2').value='';}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';setTimeout(function(){msg.style.display='none';},3000);}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
var _cpUid=0;
function adminChangePwd(uid){ _cpUid=uid; document.getElementById('changePasswordModal').style.display='flex'; document.getElementById('cpUserInfo').textContent='用户ID: '+uid; document.getElementById('cpNewPwd').value=''; document.getElementById('cpMsg').style.display='none'; }
function submitAdminChangePwd(){ var newP=document.getElementById('cpNewPwd').value; var msg=document.getElementById('cpMsg'); msg.style.display='none'; if(newP.length<4){msg.textContent='新密码至少4个字符';msg.style.display='block';return;} fetch('/admin/user/'+_cpUid+'/change_password',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:newP})}).then(function(r){return r.json();}).then(function(d){if(d.ok){msg.textContent='密码已修改';msg.style.color='#27ae60';setTimeout(function(){document.getElementById('changePasswordModal').style.display='none';},1500);}else{msg.textContent=d.detail||'修改失败';msg.style.color='#e74c3c';}msg.style.display='block';}).catch(function(){msg.textContent='请求失败';msg.style.color='#e74c3c';msg.style.display='block';}); }
```

### 5.4 改密码前端 UI（模态框 HTML）

在 `_ADMIN` 模板的 `</body>` 前插入：

```html
<!-- Profile Modal -->
<div id="profileModal" class="modal" style="display:none">
  <div class="modal-content" style="max-width:420px">
    <span class="modal-close" onclick="closeProfile()">&times;</span>
    <h3>个人资料</h3>
    <div class="form-group"><label>用户名</label><input id="profModalUser" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div>
    <div class="form-group"><label>显示名称</label><input id="profModalDN" type="text" placeholder="输入显示名称"></div>
    <div class="form-group"><label>角色</label><input id="profModalRole" type="text" readonly style="background:#f5f5f5;cursor:not-allowed"></div>
    <button class="btn" onclick="saveProfileModal()">保存</button>
    <div id="profModalSaveMsg" class="msg" style="display:none"></div>
    <hr>
    <h4>修改密码</h4>
    <div class="form-group"><label>旧密码</label><input id="profModalOldPwd" type="password" placeholder="输入旧密码"></div>
    <div class="form-group"><label>新密码</label><input id="profModalNewPwd" type="password" placeholder="至少4个字符"></div>
    <div class="form-group"><label>确认新密码</label><input id="profModalNewPwd2" type="password" placeholder="再次输入"></div>
    <button class="btn" onclick="submitProfilePwdModal()">修改密码</button>
    <div id="profModalPwdMsg" class="msg" style="display:none"></div>
  </div>
</div>
<!-- Admin Change Password Modal -->
<div id="changePasswordModal" class="modal" style="display:none">
  <div class="modal-content" style="max-width:380px">
    <span class="modal-close" onclick="document.getElementById('changePasswordModal').style.display='none'">&times;</span>
    <h3>修改用户密码</h3>
    <p id="cpUserInfo" style="color:#666;margin-bottom:12px;font-size:13px"></p>
    <div class="form-group"><label>新密码</label><input id="cpNewPwd" type="password" placeholder="至少4个字符"></div>
    <button class="btn" onclick="submitAdminChangePwd()">确认修改</button>
    <div id="cpMsg" class="msg" style="display:none"></div>
  </div>
</div>
```

### 5.5 侧边栏加"个人资料"入口

在用户管理菜单前插入：
```html
<li class="nav-item" data-page="page-profile" onclick="openProfile()">
  <span class="nav-icon">👤</span>
  <span class="nav-text">个人资料</span>
</li>
```

### 5.6 user 表加密码列+按钮

表头加 `<th style="width:100px">密码</th>`，每行加：
```html
<button class="btn-small btn-pwd" onclick="adminChangePwd(${user.id})">修改密码</button>
```

---

## 六、踩坑汇编 🐛

### 🔴 致命坑

| 坑 | 现象 | 原因 | 解决 |
|----|------|------|------|
| **SECRET_KEY 随机** | 容器重启后无法登录 | `secrets.token_hex(32)` 每次生成不同值 | **固定 SECRET_KEY** |
| **profileModal 不显示** | 点击用户名没反应 | Modal HTML 嵌套在 `display:none` 的 tab 里 | 把 modal `<div>` 移到 `<body>` 下 |
| **502 部署失败** | Railway 返回 502 | 1) Python 语法错误 2) 模板引号匹配 3) 大文件部署超时 | `ast.parse()` 本地验证 + 不要超过90KB |
| **用户管理空** | 侧边栏点用户管理没内容 | _ADMIN 模板太旧，不含用户管理功能 | 确保使用~85KB的大版本 |
| **`\` 被吃掉** | JS 语法错误 | Python `"""...\\"..."""` 处理 `\` | 外层用单引号避开 |

### 🟡 易错点

1. **Git 推完等部署**：Push 到 GitHub 后，Railway 自动重新部署约需 **60-90 秒**，期间 502 正常
2. **Force push 丢历史**：`git push --force` 会丢失远程 history，040d9dd 等旧 commit 彻底不可恢复
3. **`git add -f` 才生效**：如果 `railway_file_server.py` 被 .gitignore，普通 `git add` 不生效
4. **GitHub API 限流**：未认证 60次/小时，加 token 后 5000次/小时

---

## 七、SQLite 分支的 init_db 迁移 Bug

### 问题描述

在 SQLite 分支（`else:` 块），代码在创建 `files` 表**之前**就执行 `ALTER TABLE files`：

```python
# 代码顺序（行号供参考）
cur = conn.execute("PRAGMA table_info(files)")   # ← files 表可能还不存在
cols = [r[1] for r in cur.fetchall()]
if 'user_id' not in cols:
    conn.execute('ALTER TABLE files ADD COLUMN ...')  # ← files 不存在会报错
# ... 中间 ...
if not cols:
    conn.execute('CREATE TABLE IF NOT EXISTS files ...')  # ← 晚了！
```

### 修复方法

把 `PRAGMA table_info(files)` 放到 `CREATE TABLE IF NOT EXISTS files` **之后**。

### 影响

- **线上 PG 分支不受影响**（`information_schema.columns` 会对不存在的表抛异常 → try/except 捕获）
- **本地 SQLite** 首次启动时可能会报 `no such table: files`

---

## 八、部署后更新流程

```bash
# 1. 修改 railway_file_server.py
# 2. 验证语法
python -c "import ast; ast.parse(open('railway_file_server.py').read()); print('OK')"

# 3. 提交 + 推送
git add -f railway_file_server.py
git commit -m "描述改动"
git push origin main

# 4. 等 60-90 秒部署完成
# 5. 验证
curl https://your-domain.up.railway.app/ | head -c 200
```

如要**强制触发重新部署**（没改代码时）：
```bash
git commit --allow-empty -m "trigger redeploy"
git push origin main
```

---

## 九、交付清单

给客户交付时确认：

- [ ] GitHub 私有仓库（代码）
- [ ] Railway 项目 + 公网域名
- [ ] 管理员账号：`admin / admin123`（建议改密码）
- [ ] SECRET_KEY 已固定
- [ ] 域名（可选）
- [ ] 基本功能验证：
  - [ ] 登录/注册/登出
  - [ ] 文件上传/下载/删除
  - [ ] 用户管理（admin）
  - [ ] 修改密码（个人 + 管理员）
  - [ ] CloudData 存储

---

## 十、技术栈速查

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| 数据库 | PostgreSQL（asyncpg）/ SQLite（sqlite3） |
| 前端 | 内联 HTML + CSS + JS（SPA） |
| 部署 | Railway |
| 源码 | GitHub 私有仓库 |
| 文件存储 | 本地文件系统（UPLOAD_DIR） |
| Python 版本 | 3.11+ |
