import urllib.request, json, base64

TOKEN = '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'
headers = {'Authorization':'Bearer '+TOKEN, 'User-Agent': 'python'}

req = urllib.request.Request('https://api.github.com/repos/qiezibot/qiezidata/contents/railway_file_server.py', headers=headers)
r = json.loads(urllib.request.urlopen(req).read())
content = base64.b64decode(r['content']).decode('utf-8')
print(f'Original: {len(content)} bytes')

# STEP 1: Add nav item only
idx = content.find('<span class="nav-text">\u4e91\u6570\u636e</span>')
end_nav = content.find('</a>', idx) + 4

api_nav_line = '\r\n<a class="nav-item" href="#" onclick="switchPage(\'apidocs\',this)"><span class="nav-icon" style="font-size:18px">\U0001f4d6</span><span class="nav-text">API\u6587\u6863</span></a>'
step1 = content[:end_nav] + api_nav_line + content[end_nav:]

with open('step1_nav.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(step1)
print(f'Step 1 (nav only): {len(step1)} bytes')

# Compile check
try:
    code_part = step1[step1.find('"""')+3:]
    code_part = code_part[code_part.find('"""')+3:]
    compile(code_part, 'step1', 'exec')
    print('  Syntax: OK')
except SyntaxError as e:
    print(f'  Syntax ERROR at line {e.lineno}: {e.msg}')
    lines = code_part.split('\n')
    for i in range(max(0,e.lineno-3), min(len(lines), e.lineno+2)):
        print(f'    {i+1}: {lines[i][:120]}')
