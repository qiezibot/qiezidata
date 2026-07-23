"""Check deployed page content for our changes"""
import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    allow_redirects=True)
html = s.get('https://qiezidata-production.up.railway.app/', 
    headers={'Cache-Control': 'no-cache'}).text

print(f'Size: {len(html)}')
print(f'Contains data-open-profile: {("data-open-profile" in html)}')
print(f'Contains DOMContentLoaded.openProfile: {("DOMContentLoaded" in html and "openProfile" in html[html.find("DOMContentLoaded"):html.find("DOMContentLoaded")+200])}')
print(f'onclick=openProfile: {html.count("onclick=openProfile")}')
oc = html.count('onclick="openProfile()"')
print(f'onclick="openProfile()": {oc}')

# Check the script that has openProfile
import re
for m in re.finditer(r'DOMContentLoaded', html):
    print(f'\nDOMContentLoaded at {m.start()}: {html[m.start():m.end()+100]}')
