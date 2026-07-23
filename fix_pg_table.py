c = open('railway_file_server.py','r',encoding='utf-8').read()

# Add clouddata_projects table creation right before the 'else:' in init_db
pg_before_else = "\n            if not cols:\n                await conn.execute('CREATE TABLE IF NOT EXISTS files"
pg_insert_code = '''
            # clouddata_projects table
            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id SERIAL PRIMARY KEY,name VARCHAR(255) NOT NULL,token VARCHAR(64) NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            try:
                await conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER REFERENCES clouddata_projects(id) DEFAULT 1")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN name VARCHAR(255) DEFAULT ''")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN md5 VARCHAR(32) DEFAULT ''")
            except:
                pass
'''

c = c.replace(pg_before_else, pg_insert_code + pg_before_else)
print('PG clouddata_projects added')

# Also add default project insertion (migrate old data if needed)
default_project_code = '''
            # Ensure default project exists and migrate old data
            try:
                cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata_projects")
                if cnt == 0:
                    await conn.execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", 'default', 'default_token')
                    old_cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata")
                    if old_cnt > 0:
                        await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects WHERE name='default')")
                # Ensure old data has project_id
                await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects LIMIT 1) WHERE project_id IS NULL")
            except:
                pass
'''
# Insert after the files table creation (before the closing of async with block)
pg_post_files = "await conn.execute('UPDATE files SET user_id = $1 WHERE user_id IS NULL', aid)"
c = c.replace(pg_post_files, pg_post_files + default_project_code)
print('Default project migration added')

# Also fix SQLite - need to handle SQLite default project
sq_default_code = '''
            # Ensure default project exists
            try:
                cnt = conn.execute("SELECT COUNT(*) FROM clouddata_projects").fetchone()[0]
                if cnt == 0:
                    conn.execute("INSERT INTO clouddata_projects (name,token,created_at) VALUES (?,?,?)", ('default', 'default_token', datetime.utcnow().isoformat()))
                    conn.commit()
            except:
                pass
'''
sq_post_files = "conn.execute('UPDATE files SET user_id = ? WHERE user_id IS NULL', (aid,))"
c = c.replace(sq_post_files, sq_post_files + sq_default_code)
print('SQLite default project added')

# Verify
assert 'clouddata_projects' in c[c.find('init_db'):c.find('async def', c.find('init_db')+30)], 'projects table NOT in init_db!'
assert 'cloudDataBody' in c, 'Frontend missing!'

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('ALL OK size:', len(c))
