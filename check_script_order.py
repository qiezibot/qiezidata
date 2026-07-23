"""Check if the inline scripts execute properly and in what order"""
import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    allow_redirects=True)
html = s.get('https://qiezidata-production.up.railway.app/', headers={'Cache-Control': 'no-cache'}).text

# Find all scripts and their positions
print('Script blocks and their positions in page:')
import re
for m in re.finditer(r'<script>(.*?)</script>', html, re.DOTALL):
    pos = m.start()
    content = m.group(1).strip()
    preview = content[:100].replace('\n', ' ')
    print(f'  pos={pos}, len={len(content)}: {preview}...')
    # Check if this script has syntax issues
    # Just look for open/close braces balance
    opens = content.count('{')
    closes = content.count('}')
    if opens != closes:
        print(f'    ⚠️ Brace mismatch: {opens} vs {closes}')

# Check if there are any JS syntax errors by looking for common patterns
# Also check if any script runs before openProfile is defined
# The function is defined at pos 32847 (script block 1)
script1_pos = html.find('function openProfile')
print(f'\nopenProfile function at page pos: {script1_pos}')

# Find where the onclick elements are
for i in range(2):
    oc_pos = html.find('onclick="openProfile()"')
    if oc_pos >= 0:
        print(f'  onclick at page pos: {oc_pos}')
        # Check if it's before or after the function
        rel = 'BEFORE' if oc_pos < script1_pos else 'AFTER'
        print(f'  -> This onclick element is {rel} the function definition')
        html = html[:oc_pos] + 'X' + html[oc_pos+1:]  # mark as found

# Check the overall HTML order
print(f'\nOverall HTML structure (summary):')
print(f'  <body> tag')
body_pos = html.find('<body>')
sw_pos = html.find('switchPage')
nav_pos = html.find('<div class="nav-')
oc_pos = html.find('onclick=')
print(f'  <body> tag at position {body_pos}')
print(f'  ... {sw_pos - body_pos} chars after <body> → first script (switchPage etc)')
print(f'  ... {nav_pos - body_pos} chars after <body> → sidebar HTML (nav)')
print(f'  ... {"?" if oc_pos < 0 else oc_pos - body_pos} chars after <body> → onclick elements')
