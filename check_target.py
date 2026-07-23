c = open('railway_file_server.py','r',encoding='utf-8').read()
i = c.find('init_db')
j = c.find('async def', i+30)
init_content = c[i:j]

# What does the PG branch actually have?
pg_read_line_idx = init_content.find("read BOOLEAN NOT NULL DEFAULT FALSE')")
print('PG read line check:', repr(init_content[pg_read_line_idx:pg_read_line_idx+50]))

# What am I looking for?
target = "BOOLEAN NOT NULL DEFAULT FALSE')"
print('Target string:', repr(target))
print('Found at:', init_content.find(target))
