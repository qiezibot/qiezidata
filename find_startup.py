import subprocess
out = subprocess.check_output(['git', 'cat-file', '-p', '8c6fc931d7f71a947f5e0b0bd18f39d476b8e474:railway_file_server.py'])
c = out.decode('utf-8')
# 找 startup
import re
for m in re.finditer(r"@app\.on_event\('startup'\)", c):
    print(c[m.start():m.start()+3000])
