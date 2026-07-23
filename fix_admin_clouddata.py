c = open('railway_file_server.py', 'r', encoding='utf-8').read()
# Fix clouddata_list: db_execute -> db_fetch (PostgreSQL and SQLite branches)
old_pg = "return await db_execute(\"SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata ORDER BY id DESC\")"
new_pg = "return await db_fetch(\"SELECT id,k,v,to_char(t,'YYYY-MM-DD HH24:MI') AS t,read FROM clouddata ORDER BY id DESC\")"
old_sq = "return await db_execute('SELECT id,k,v,t,read FROM clouddata ORDER BY id DESC')"
new_sq = "return await db_fetch('SELECT id,k,v,t,read FROM clouddata ORDER BY id DESC')"

print('PG branch found:', old_pg in c)
print('SQ branch found:', old_sq in c)

c = c.replace(old_pg, new_pg)
c = c.replace(old_sq, new_sq)

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK')
