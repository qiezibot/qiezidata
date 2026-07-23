"""Check what happened - login page or broken admin?"""
import requests

s = requests.Session()
r = s.post('https://qiezidata-production.up.railway.app/login', 
    data={'username': 'admin', 'password': 'admin123'},
    allow_redirects=False)
print(f'Login status: {r.status_code}')
print(f'Location: {r.headers.get("Location")}')
print(f'Cookies: {dict(s.cookies)}')

r2 = s.get('https://qiezidata-production.up.railway.app/', headers={'Cache-Control': 'no-cache'})
print(f'Admin page: {r2.status_code}, {len(r2.text)} bytes')

# Check if <body> is even there
if '<body>' in r2.text:
    print('Has <body> tag - OK')
else:
    print('NO <body> tag!')

# Check modal positions
for tag in ['profileModalDummy', 'profileModal', 'pwdModal']:
    pos = r2.text.find(tag)
    if pos >= 0:
        print(f'{tag} at pos {pos}: ...{r2.text[max(0,pos-30):pos+100]}...')
    else:
        print(f'{tag}: MISSING!')

# Check if there's a login redirect
if 'login' in r2.url.lower() or 'login' in r2.text.lower()[:1000]:
    print('Being redirected to login page!')
    print(r2.text[:500])
