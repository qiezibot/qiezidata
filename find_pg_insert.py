c = open('railway_file_server.py','r',encoding='utf-8').read()

# Find PG branch end in init_db (where files table creation begins)
init_i = c.find('async def init_db')
init_j = c.find('async def', init_i+30)
init_body = c[init_i:init_j]

pg_i = init_body.find('if use_pg:')
else_i = init_body.find('\n    else:')
pg_body = init_body[pg_i:else_i]

# Find the right spot: after all PG table creation code
# Look for the last conn.execute for files table in PG
pg_files_end = pg_body.rfind('conn.execute(')
print('Last conn.execute in PG at:', pg_files_end)
print('Context:', repr(pg_body[pg_files_end:pg_files_end+200]))

# Also check if files table creation in PG has `if not cols:` block
pg_end_content = pg_body[-400:]
print('PG end 400:', repr(pg_end_content))

# Add clouddata_projects before files table creation
# Insert after the 'read' column migration
pg_insert_point = pg_body.find("ALTER TABLE clouddata ADD COLUMN read BOOLEAN")
pg_insert_line_end = pg_body.find('\n', pg_insert_point)
pg_insert_line_end2 = pg_body.find('\n', pg_insert_line_end+1)
print('Insert after (around pg line):', repr(pg_body[pg_insert_line_end:pg_insert_line_end+200]))
