import requests

s = requests.Session()
s.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'})
html = s.get('https://qiezidata-production.up.railway.app/').text

# Extract Block 0 (the big one)
# Find by /* v3 */
v3_pos = html.find('/* v3 */')
if v3_pos < 0:
    v3_pos = html.find('function switchPage')
    
ss = html.rfind('<script>', 0, v3_pos)
se = html.find('</script>', v3_pos)
block0 = html[ss+8:se]

print(f'Block 0: {len(block0)} bytes')

# Extract Block 1
# Find by var pwdModalTargetUid = null
pwd_var = html.find('var pwdModalTargetUid')
if pwd_var < 0:
    print("Could not find block 1 start")
else:
    ss1 = html.rfind('<script>', 0, pwd_var)
    se1 = html.find('</script>', pwd_var)
    block1 = html[ss1+8:se1]
    print(f'Block 1: {len(block1)} bytes')

# Write to files for Node.js syntax check
import os

outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp_js')
os.makedirs(outdir, exist_ok=True)

with open(os.path.join(outdir, 'block0.js'), 'w', encoding='utf-8') as f:
    f.write(block0)
with open(os.path.join(outdir, 'block1.js'), 'w', encoding='utf-8') as f:
    f.write(block1)

print(f'Files written to {os.path.join(outdir, "block0.js")} and block1.js')
