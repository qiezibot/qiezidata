c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find exact position to insert PG clouddata_projects
# We need to insert inside the PG branch in init_db
init_i = c.find('async def init_db')
init_j = c.find('async def', init_i+30)
init_body = c[init_i:init_j]

pg_end_marker = "file_path VARCHAR(512) NOT NULL)')"
pg_end_i = init_body.find(pg_end_marker)
if pg_end_i < 0:
    print('ERROR: PG end marker not found')
else:
    print('PG end at', pg_end_i)
    # Insert after PG files table creation + migration completes
    # The PG branch ends at '\n    else:'
    else_marker = '\n    else:'
    else_i = init_body.find(else_marker, pg_end_i)
    print('else at', else_i)
    
    insert_code = '''
            # clouddata_projects
            await conn.execute('CREATE TABLE IF NOT EXISTS clouddata_projects(id SERIAL PRIMARY KEY,name VARCHAR(255) NOT NULL,token VARCHAR(64) NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            try:
                await conn.execute("ALTER TABLE clouddata ADD COLUMN project_id INTEGER REFERENCES clouddata_projects(id) DEFAULT 1")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN name VARCHAR(255) DEFAULT ''")
                await conn.execute("ALTER TABLE clouddata ADD COLUMN md5 VARCHAR(32) DEFAULT ''")
            except: pass
            try:
                cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata_projects")
                if cnt == 0:
                    await conn.execute("INSERT INTO clouddata_projects (name,token) VALUES ($1,$2)", 'default', 'default_token')
                    old_cnt = await conn.fetchval("SELECT COUNT(*) FROM clouddata")
                    if old_cnt > 0:
                        await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects WHERE name='default')")
                await conn.execute("UPDATE clouddata SET project_id = (SELECT id FROM clouddata_projects LIMIT 1) WHERE project_id IS NULL")
            except: pass
'''
    new_init_body = init_body[:else_i] + insert_code + init_body[else_i:]
    c = c[:init_i] + new_init_body + c[init_j:]
    
    open('railway_file_server.py', 'w', encoding='utf-8').write(c)
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('DONE, size:', len(c))
    
    # Verify
    i2 = c.find('init_db')
    j2 = c.find('async def', i2+30)
    body2 = c[i2:j2]
    print('PG has clouddata_projects:', 'clouddata_projects' in body2[:body2.find('\n    else:')] if '\n    else:' in body2 else 'N/A')
