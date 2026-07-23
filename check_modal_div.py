"""Check if profileModal div exists in deployed page"""
import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    allow_redirects=True)
html = s.get('https://qiezidata-production.up.railway.app/', headers={'Cache-Control': 'no-cache'}).text

# Check for div
for tag in ['<div id="profileModal"', 'id="profileModal"', '<div id="profileModalDummy"', 'id="profileModalDummy"']:
    idx = html.find(tag)
    if idx >= 0:
        print(f'FOUND "{tag}" at {idx}: ...{html[max(0,idx-50):idx+200]}...')
    else:
        print(f'NOT FOUND: "{tag}"')

# Check total structure
print(f'\nTotal size: {len(html)}')
print(f'Total script blocks: {len([t for t in range(len(html)) if html[t:t+8] == "<script>"])}')
print(f'openProfile function defs: {html.count("function openProfile")}')
oc = html.count('onclick="openProfile()"')
print(f'openProfile onclick attrs: {oc}')

# Check if there's a CSS rule that hides modals
if 'profileModal' in html:
    print('\nprofileModal CSS rules:')
    import re
    # Find between style tags
    for m in re.finditer(r'<style>(.*?)</style>', html, re.DOTALL):
        css = m.group(1)
        if 'profileModal' in css:
            print(f'  FOUND in CSS: {css[css.find("profileModal"):css.find("profileModal")+80]}')
