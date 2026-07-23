import subprocess, sys

# Check all commits that have change_password in the file
lines = subprocess.check_output(['git', 'log', '--oneline', '--all']).decode().strip().split('\n')
for line in lines:
    sha = line.split()[0]
    try:
        out = subprocess.check_output(['git', 'show', sha+':railway_file_server.py'])
        c = out.decode('utf-8')
        if 'change_password' in c:
            print(f'{sha} {len(out)} bytes - HAS change_password')
            has_profile = 'profileModal' in c or 'openProfile' in c or 'old_password' in c
            has_ui = 'passwordModal' in c or 'pwdm' in c or 'pwdModal' in c
            print(f'  Profile: {has_profile}, UI: {has_ui}')
    except:
        pass
