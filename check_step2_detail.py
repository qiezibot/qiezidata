import sys, ast

with open('railway_file_server_local.py', 'r', encoding='utf-8') as f:
    original = f.read()

idx1 = original.find('"""')
idx2 = original.find('"""', idx1+3) + 3

# Step1: add nav in docstring area
nav_idx = original.find('<span class="nav-text">\u4e91\u6570\u636e</span>')
end_nav = original.find('</a>', nav_idx) + 4
nav_line = '\r\n<a class="nav-item" href="#" onclick="switchPage(\'apidocs\',this)"><span class="nav-icon" style="font-size:18px">\U0001f4d6</span><span class="nav-text">API\u6587\u6863</span></a>'
step1 = original[:end_nav] + nav_line + original[end_nav:]

# Step2: api page
idx_toast = step1.find('<div id="toast"')
api_html = ('<div class="tab-page" id="page-apidocs">\n'
    '<div class="card" style="background:#e8f4fd;padding:15px">\n'
    '<h3 style="margin-top:0">\U0001f4d6 API \u5bf9\u63a5\u6587\u6863</h3>\n'
    '<p style="color:#666;font-size:14px">\u4ee5\u4e0b\u63a5\u53e3\u4f9b\u7b2c\u4e09\u65b9\u5f00\u53d1\u8005\u5bf9\u63a5\u4f7f\u7528\uff0c\u9700\u8981\u5148\u83b7\u53d6 Access Token\u3002</p>\n\n'
    '<h4 style="margin:15px 0 5px">1. \u83b7\u53d6\u6570\u636e\u5217\u8868</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=-1<br>\n'
    '<span style="color:#999">\u53c2\u6570\uff1aproject_id=\u9879\u76eeID, token=\u9879\u76eeToken, queryType=-1\u5168\u90e8/0\u672a\u8bfb/1\u5df2\u8bfb</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">2. \u83b7\u53d6\u5355\u6761\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{data_id}?token={token}<br>\n'
    '<span style="color:#999">\u8fd4\u56de\u8be5\u6761\u6570\u636e\u7684\u539f\u59cb\u5185\u5bb9\uff08\u7eaf\u6587\u672c\uff09</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">3. \u4e0a\u4f20\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>POST</strong> /api/cddata/{project_id}?token={token}<br>\n'
    '<span style="color:#999">Body (JSON): {"key": "xxx", "value": "xxx"}</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">4. \u6807\u8bb0\u6570\u636e\u72b6\u6001</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>POST</strong> /api/cddata/state/{data_id}?token={token}<br>\n'
    '<span style="color:#999">\u5207\u6362\u8be5\u6761\u6570\u636e\u7684\u5df2\u8bfb/\u672a\u8bfb\u72b6\u6001</span>\n'
    '</div>\n\n'
    '<h4 style="margin:15px 0 5px">5. \u5220\u9664\u6570\u636e</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>DELETE</strong> /api/cddata/{data_id}?token={token}\n'
    '</div>\n\n'
    '<br>\n'
    '<h4 style="color:#e74c3c">\u83b7\u53d6 Token</h4>\n'
    '<p style="font-size:13px;color:#666">\u5728\u4e91\u6570\u636e\u9875\u9762\u521b\u5efa\u9879\u76ee\u540e\uff0c\u9879\u76ee\u8be6\u60c5\u4e2d\u4f1a\u663e\u793a\u5bf9\u5e94\u7684 Token\u3002<br>\n'
    'Token \u7528\u4e8e\u9274\u6743\uff0c\u8bf7\u59a5\u5584\u4fdd\u7ba1\u3002</p>\n'
    '</div>\n</div>\n\n')

step2 = step1[:idx_toast] + api_html + step1[idx_toast:]

# Now extract code portion and AST/compile check
code = step2[idx2:]

print(f'Total file: {len(step2)} bytes')
print(f'Code portion: {len(code)} bytes')
print(f'Docstring region: {idx2} bytes')

# Count { } patterns in code to find potential f-string issues
bc_count = code.count('{')
print(f'Open braces in code: {bc_count}')
bc_close = code.count('}')
print(f'Close braces in code: {bc_close}')

# Check for {project_id} specifically
if '{project_id}' in code:
    idx = code.find('{project_id}')
    print(f'\nFirst {{project_id}} at pos {idx} in CODE section!')
    print(f'Context: {repr(code[idx-80:idx+80])}')

# Check for {token}
if '{token}' in code:
    idx = code.find('{token}')
    print(f'\nFirst {{token}} at pos {idx} in CODE section!')
    print(f'Context: {repr(code[idx-80:idx+80])}')

print()

try:
    tree = ast.parse(code)
    print('AST parse: OK')
except SyntaxError as e:
    print(f'AST ERROR line {e.lineno}: {e.msg}')
    lines = code.split('\n')
    start = max(0, e.lineno-3)
    end = min(len(lines), e.lineno+2)
    for i in range(start, end):
        print(f'  {i+1}: {lines[i][:120]}')

try:
    compile(code, 'step2', 'exec')
    print('compile(): OK')
except SyntaxError as e:
    print(f'compile ERROR line {e.lineno}: {e.msg}')
