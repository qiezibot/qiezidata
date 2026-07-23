import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Find where profileModalDummy appears
pos = html.find('profileModalDummy')
print(f'profileModalDummy at {pos}')
if pos > 0:
    print(f'Context: ...{html[pos-50:pos+150]}...')

# Find where real profileModal appears
pid = html.find('id="profileModal"')
print(f'\nid="profileModal" at {pid}')
if pid > 0:
    print(f'Context: ...{html[pid-50:pid+150]}...')

# Find all script tag positions
script_starts = []
i = 0
while True:
    s = html.find('<script>', i)
    if s < 0: break
    e = html.find('</script>', s)
    if e < 0: break
    script_starts.append((s, e))
    i = e + 9

# Check which script block each div is before
for sidx, (ss, se) in enumerate(script_starts):
    if pos < ss:
        print(f'\nDummy is BEFORE script block {sidx} (starts at {ss})')
        print(f'Gap: {ss - pos} chars')
        break
    else:
        print(f'\nDummy is AFTER or INSIDE script block {sidx}')

for sidx, (ss, se) in enumerate(script_starts):
    if pid < ss:
        print(f'\nReal profileModal is BEFORE script block {sidx} (starts at {ss})')
        print(f'Gap: {ss - pid} chars')
        # Print everything between real profileModal and that script
        between = html[pid:ss]
        print(f'Between profileModal and script: {len(between)} chars')
        print(f'Content: ...{between[:200]}...')
        break
    else:
        print(f'\nReal profileModal is AFTER or INSIDE script block {sidx}')
