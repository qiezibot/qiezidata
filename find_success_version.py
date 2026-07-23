import subprocess, sys

commits = [
    '332c951', '9a74f05', '8c6fc93', 'a08194d', '86c7782',
    'da65b19', 'ddfaff7', '7edeb88', 'bb56d8f', 'a77913c',
    '835e92d', 'f2d0880', 'e6da2ad', 'f07500a', '332c951'
]

for sha in set(commits):
    try:
        out = subprocess.check_output(['git', 'show', sha+':railway_file_server.py'])
        c = out.decode('utf-8')
        # Check size and features
        has_cp_route = '/change_password' in c
        has_profile = '/me' in c and 'POST' in c
        has_pwd_ui = 'passwordModal' in c or 'pwdModal' in c or 'aCP(' in c
        has_profile_ui = 'profileModal' in c or 'pO(' in c
        print(f'{sha}: {len(out)} bytes, cpRoute={has_cp_route}, profile={has_profile}, pwdUI={has_pwd_ui}, profileUI={has_profile_ui}')
    except:
        print(f'{sha}: NOT FOUND')
