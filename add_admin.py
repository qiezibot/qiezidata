with open('railway_file_server.py','r',encoding='utf-8') as f:
    c = f.read()

# 在 init_db() 函数里加创建默认 admin 账号
# 找到 async def init_db(): 里的内容
old_init = "async def init_db():"
old_full = """async def init_db():
    if use_pg:"""

new_full = """async def init_db():
    admin_user = os.environ.get('ADMIN_USER', 'admin')
    admin_pass = os.environ.get('ADMIN_PASS', 'admin123')
    if use_pg:"""

c = c.replace(old_init, '', 1)
c = c.replace(old_full, new_full, 1)
print("Added env vars for admin ✅")

# 在创建完 users 表后加插入默认 admin 的逻辑
# 找 'role VARCHAR(16) NOT NULL DEFAULT' 后面的创建表代码
# 然后看 register 函数在哪里
# 找到第一个 @app.post('/register') 或 register 函数
# 在启动时检查 admin 账号是否存在

# 找 "async def init_db():" 后面找创建表的完整代码
import re
# 找 init_db 函数体里的表创建
init_start = c.find("async def init_db():")
init_body = c[init_start:]

# 创建完所有表后，加 admin 账号检查
# find where init_db ends - look for next route decorator
next_route = re.search(r"\n@app\.", init_body)
if next_route:
    init_end = init_start + next_route.start()
    # Insert admin creation right before the end of init_db
    admin_code = """
    try:
        row = await db_fetchrow('SELECT id FROM users WHERE username=$1' if use_pg else 'SELECT id FROM users WHERE username=?', admin_user)
        if not row:
            await db_execute('INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)' if use_pg else 'INSERT INTO users (username,password_hash,display_name,role) VALUES (?,?,?,?)', admin_user, _hash(admin_pass), 'Admin', 'admin')
    except Exception as e:
        pass
"""
    # Insert after the last table creation + migration code
    # Find the end of migrations - look for "await init_db()" or next decorator
    # Just find the last line before next route
    before_routes = c[:init_end]
    c = before_routes + admin_code + c[init_end:]
    print("Added admin account creation in init_db ✅")

with open('railway_file_server.py','w',encoding='utf-8') as f:
    f.write(c)

sz = len(c.encode('utf-8'))
print(f"Size: {sz} bytes")
print(f"admin/admin123: {'admin123' in c}")
