c = open('railway_file_server.py', 'r', encoding='utf-8').read()
old_line = "if(id==='clouddata')loadCloudData()"
new_line = "if(id==='clouddata')initCloudData()"
assert old_line in c, 'switchPage line not found!'
c = c.replace(old_line, new_line)
open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('Fixed switchPage, size:', len(c))
