import sys
sys.stdout.reconfigure(encoding='utf-8')
c = open('railway_file_server.py', encoding='utf-8').read()
html = c[37522:67150]
test = ")+'</td></tr>'"
pos = html.find(test)
if pos >= 0:
    print(f'Found at {pos}: {repr(html[pos:pos+120])}')
else:
    # maybe template literal or different pattern
    for pat in ["+'</td></tr>'", "'</td></tr>'"]:
        p = html.find(pat)
        if p >= 0:
            print(f'With "{pat}" at {p}: {repr(html[p:p+120])}')
