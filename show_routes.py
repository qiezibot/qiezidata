import subprocess
out = subprocess.check_output(['git', 'show', 'a08194d:railway_file_server.py'])
c = out.decode('utf-8')
lines = c.split('\n')
for i, l in enumerate(lines):
    if '@app.' in l and 'def ' in l:
        print(f'{i}: {l.strip()}')
