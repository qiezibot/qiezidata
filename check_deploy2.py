import requests, re, sys, subprocess, json
sys.stdout.reconfigure(encoding='utf-8')

session = requests.Session()
session.post('https://qiezidata-production.up.railway.app/login', data={'username':'admin','password':'admin123'}, allow_redirects=False)
r = session.get('https://qiezidata-production.up.railway.app/')

scripts = re.findall(r'<script>(.*?)</script>', r.text, re.DOTALL)
script = scripts[0]

# Save to temp file
with open('C:\\temp\\deployed_script.js', 'w', encoding='utf-8') as f:
    f.write(script)

# Validate via Node
result = subprocess.run(
    ['node', '-e', 'try { new Function(require("fs").readFileSync("C:\\\\temp\\\\deployed_script.js","utf8")); console.log("VALID"); } catch(e) { console.log("ERROR:", e.message); }'],
    capture_output=True, text=True, timeout=10
)
print(f'Node validation: {result.stdout.strip()}')
if result.stderr:
    print(f'Node stderr: {result.stderr}')

# Also check for the event delegation listener
idx = script.find('addEventListener')
print(f'\nEvent listener: {script[idx:idx+300]}')
