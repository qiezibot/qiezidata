c = open('railway_file_server.py','r',encoding='utf-8').read()
i = c.find('init_db')
j = c.find('async def', i+30)
init_content = c[i:j]

# Find PG "read" line
pg_read = init_content.find("read BOOLEAN NOT NULL DEFAULT FALSE")
print('PG read at:', pg_read)
print('Context:', repr(init_content[pg_read:pg_read+150]) if pg_read >=0 else 'NOT FOUND')

# Count PG and SQLite sections
pg_else = init_content.find("\n    else:")
print('else at:', pg_else)
print('PG section length:', pg_else if pg_else >= 0 else 'N/A')
print()
print('====== PG SECTION ======')
print(init_content[:2000])
