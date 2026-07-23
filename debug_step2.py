with open('railway_file_server_local.py', 'r', encoding='utf-8') as f:
    original = f.read()

# Step1: add nav (increases length)
nav_idx = original.find('<span class="nav-text">\u4e91\u6570\u636e</span>')
end_nav = original.find('</a>', nav_idx) + 4
nav_line = '\r\n<a class="nav-item" href="#" onclick="switchPage(\'apidocs\',this)"><span class="nav-icon" style="font-size:18px">\U0001f4d6</span><span class="nav-text">API\u6587\u6863</span></a>'
step1 = original[:end_nav] + nav_line + original[end_nav:]

# Find docstring in step1
idx1_new = step1.find('"""')
idx2_new = step1.find('"""', idx1_new+3)
print(f'Original idx2: 1328')
print(f'Step1 idx2: {idx2_new}')
print(f'Shift: {idx2_new - 1328} bytes (nav insert added this much)')

# Now verify code portion starts correctly
code_step1 = step1[idx2_new+3:]
print(f'Code starts: {repr(code_step1[:50])}')

try:
    import ast
    ast.parse(code_step1)
    print('Step1 code AST: OK')
except SyntaxError as e:
    print(f'Step1 code ERROR: {e}')

# Now step2
idx_toast = step1.find('<div id="toast"')
api_html = ('<div class="tab-page" id="page-apidocs">\n'
    '<div class="card" style="background:#e8f4fd;padding:15px">\n'
    '<h3 style="margin-top:0">📖 API 对接文档</h3>\n'
    '<p style="color:#666;font-size:14px">以下接口供第三方开发者对接使用，需要先获取 Access Token。</p>\n\n'
    '<h4 style="margin:15px 0 5px">1. 获取数据列表</h4>\n'
    '<div style="background:#f5f5f5;padding:10px;border-radius:4px;font-size:13px;font-family:monospace">\n'
    '<strong>GET</strong> /api/cddata/{project_id}?token={token}&amp;queryType=-1<br>\n'
    '<span style="color:#999">参数：project_id=项目ID, token=项目Token, queryType=-1全部/0未读/1已读</span>\n'
    '</div>\n\n'
    '</div>\n</div>\n\n')

step2 = step1[:idx_toast] + api_html + step1[idx_toast:]

# Find docstring in step2
idx1_s2 = step2.find('"""')
idx2_s2 = step2.find('"""', idx1_s2+3)
print(f'\nStep2 idx2: {idx2_s2}')
print(f'Shift from original: {idx2_s2 - 1328}')

code_step2 = step2[idx2_s2+3:]
print(f'Code starts: {repr(code_step2[:50])}')

try:
    ast.parse(code_step2)
    print('Step2 code AST: OK')
except SyntaxError as e:
    print(f'Step2 code ERROR at line {e.lineno}: {e.msg}')
    lines = code_step2.split('\n')
    for i in range(max(0,e.lineno-3), min(len(lines), e.lineno+2)):
        print(f'  {i+1}: {lines[i][:120]}')
