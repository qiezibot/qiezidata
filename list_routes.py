import subprocess, re
out = subprocess.check_output(['git', 'cat-file', '-p', '8c6fc931d7f71a947f5e0b0bd18f39d476b8e474:railway_file_server.py'])
c = out.decode('utf-8')
for m in re.finditer(r"@app\.(get|post|delete)\('([^']+)'\)", c):
    print(f'{m.group(1):6} {m.group(2)}')
