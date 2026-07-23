import requests, re

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

print(f'Size: {len(html)} bytes')

modals = [m.start() for m in re.finditer(r'profileModal', html)]
print(f'profileModal occurrences: {len(modals)}')
for pos in modals:
    context = html[max(0,pos-120):pos+200]
    print(f'--- pos {pos} ---')
    print(context[:500])
    print()
