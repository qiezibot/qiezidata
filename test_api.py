import requests

# Test the change password API
resp = requests.post(
    'https://qiezidata-production.up.railway.app/me/change_password',
    cookies=requests.utils.dict_from_cookiejar(
        requests.get('https://qiezidata-production.up.railway.app/',
                     cookies=requests.post(
                         'https://qiezidata-production.up.railway.app/login',
                         data={'username': 'admin', 'password': 'admin123'}
                     ).cookies
                    ).cookies
    ),
    json={'old_password': 'admin123', 'new_password': 'admin1234'}
)
print(f'Status: {resp.status_code}')
print(f'Body: {resp.text[:200]}')

# Second request to verify
resp2 = requests.post(
    'https://qiezidata-production.up.railway.app/me/change_password',
    cookies=resp.cookies,
    json={'old_password': 'admin1234', 'new_password': 'admin123'}
)
print(f'Revert status: {resp2.status_code}')
print(f'Revert body: {resp2.text[:200]}')
