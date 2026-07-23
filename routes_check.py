import subprocess

for sha in ['a08194d', 'bb56d8f']:
    out = subprocess.check_output(['git', 'show', sha + ':railway_file_server.py'])
    c = out.decode('utf-8')
    lines = c.split('\n')
    print(f'=== {sha} ({len(out)} bytes) ===')
    for i, l in enumerate(lines):
        if '@app.' in l:
            print(f'  {i}: {l.strip()[:80]}')
    print()
