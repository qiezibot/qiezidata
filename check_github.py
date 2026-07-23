import sys
t = sys.stdin.read()
has_pwd = 'pwdModal' in t
has_prof = 'profileModal' in t
has_pwd_div = 'id="pwdModal"' in t
has_prof_div = 'id="profileModal"' in t
print(f'pwdModal: {has_pwd}')
print(f'profileModal: {has_prof}')
print(f'id="pwdModal": {has_pwd_div}')
print(f'id="profileModal": {has_prof_div}')
print(f'Size: {len(t)}')
