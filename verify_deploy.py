import requests
s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text
print(f'Size: {len(html)}')

pm = html.count('profileModal')
print(f'profileModal refs: {pm}')

pmd = html.count('profileModalDummy')
print(f'profileModalDummy refs: {pmd}')

pos = html.find('profileModalDummy')
print(f'Dummy at pos: {pos}')
if pos >= 0:
    print(html[max(0,pos-60):pos+180])

pos2 = html.find('id="profileModal"')
print(f'Real profileModal at pos: {pos2}')
if pos2 >= 0:
    print(html[max(0,pos2-60):pos2+300])
