# 修复 railway_file_server.py 的 init_db 中 files 表迁移逻辑
# 问题：当 files 表不存在时，PG 分支的 ALTER TABLE 会报错

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 PG 分支中 files 表迁移的问题代码并修复
old = """            cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='files'")
            if 'user_id' not in [c['column_name'] for c in cols]:
                await conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
                admin = await conn.fetchrow("SELECT id FROM users WHERE username='admin'")
                if not admin:
                    h = _hash('admin123')
                    await conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)", 'admin', h, 'Admin', 'admin')
                    aid = await conn.fetchval("SELECT id FROM users WHERE username='admin'")
                else: aid = admin['id']
                await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)
            if not cols:
                await conn.execute('CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL, size BIGINT NOT NULL, mime_type VARCHAR(128), upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL)')"""

new = """            try:
                cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='files'")
            except:
                cols = []
            if not cols:
                await conn.execute('CREATE TABLE IF NOT EXISTS files (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename VARCHAR(255) NOT NULL, original_name VARCHAR(255) NOT NULL, size BIGINT NOT NULL, mime_type VARCHAR(128), upload_time TIMESTAMP NOT NULL DEFAULT NOW(), file_path VARCHAR(512) NOT NULL)')
            else:
                if 'user_id' not in [c['column_name'] for c in cols]:
                    await conn.execute('ALTER TABLE files ADD COLUMN user_id INTEGER REFERENCES users(id)')
                    admin = await conn.fetchrow("SELECT id FROM users WHERE username='admin'")
                    if not admin:
                        h = _hash('admin123')
                        await conn.execute("INSERT INTO users (username,password_hash,display_name,role) VALUES ($1,$2,$3,$4)", 'admin', h, 'Admin', 'admin')
                        aid = await conn.fetchval("SELECT id FROM users WHERE username='admin'")
                    else: aid = admin['id']
                    await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)"""

if old in content:
    content = content.replace(old, new)
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('PG files table migration fixed OK')
else:
    print('Old text not found - checking if already fixed...')
    # 检查是否已经修好了
    if 'try:' in content and 'cols = await conn.fetch' in content and 'except:' in content:
        print('Already fixed')
    else:
        print('Pattern not found. Searching for alternatives...')
        import re
        # 找相关代码段
        m = re.search(r"information_schema\.columns WHERE table_name='files'", content)
        if m:
            print(f'Found at position {m.start()}')
            print(content[m.start()-50:m.start()+300])
