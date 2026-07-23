"""Deep analysis of the deployed admin HTML to find why onclick doesn't fire"""
import requests, re

# Fetch the admin page directly
s = requests.Session()
r1 = s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    headers={'Content-Type': 'application/x-www-form-urlencoded'},
    allow_redirects=True)
print(f'Login: {r1.status_code}')

r2 = s.get('https://qiezidata-production.up.railway.app/', 
    headers={'Cache-Control': 'no-cache'})
html = r2.text
print(f'Page size: {len(html)} bytes')

# Find the script blocks and locate openProfile
# Extract all <script> blocks
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
print(f'\nScript blocks: {len(scripts)}')

for i, sc in enumerate(scripts):
    if 'openProfile' in sc:
        print(f'\n=== Script block {i} (contains openProfile) ===')
        pos = sc.find('function openProfile')
        print(f'openProfile at char {pos} in this script')
        # Show first 300 chars of this script
        print(sc[max(0,pos-100):pos+400])
        print('...')

# Also check if there are other script blocks BEFORE the one with openProfile
# that might overwrite/remove onclick
for i, sc in enumerate(scripts):
    if 'openProfile' not in sc:
        if any(x in sc for x in ['onclick', 'click', 'pointer', 'event']):
            print(f'\nScript block {i} (related to clicks/events):')
            print(sc[:300])
            print('...')

# Check if the modal divs exist
for div_id in ['profileModal', 'profileModalDummy']:
    if div_id in html:
        pos = html.find(div_id)
        ctx = html[max(0,pos-50):pos+200]
        print(f'\n{div_id} at {pos}: {ctx}')
    else:
        print(f'\n{div_id}: NOT FOUND IN PAGE!')
