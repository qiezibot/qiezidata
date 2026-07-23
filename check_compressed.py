import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# 在压缩后的文件中找 loadUsers
pos = c.find('loadUsers')
if pos >= 0:
    snippet = c[pos:pos+5000]
    print(snippet[800:2500])
