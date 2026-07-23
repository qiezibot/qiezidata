import sys
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()
html = c[37522:67150]
pos = html.find('loadUsers')
if pos >= 0:
    snippet = html[pos:pos+2000]
    # Find the render line
    rpos = snippet.find("h+=")
    if rpos >= 0:
        print(snippet[rpos:rpos+1500])
