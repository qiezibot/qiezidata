import subprocess
for sha in ['86c7782', 'da65b19', 'ddfaff7', 'a08194d']:
    try:
        out = subprocess.check_output(['git', 'show', sha+':railway_file_server.py'])
        print(f'{sha}: {len(out)} bytes')
    except:
        print(f'{sha}: NOT FOUND')
