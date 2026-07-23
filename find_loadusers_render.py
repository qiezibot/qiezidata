import sys
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()

# Find the actual loadUsers render line
pos = c.find('async function loadUsers()')
if pos >= 0:
    snippet = c[pos:pos+2000]
    # Find the render part with 'h+='
    hpos = snippet.find(";h+=")
    if hpos < 0:
        hpos = snippet.find("h+=")
    if hpos >= 0:
        print(snippet[hpos:hpos+800])
