import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

# 找 JS 脚本部分
script_pos = html.rfind('<script>')
if script_pos < 0:
    script_pos = html.rfind('<script ')
if script_pos >= 0:
    print(f'Script at {script_pos}, length ~{len(html)-script_pos}')
    print(html[script_pos:script_pos+5000])
    print('...')
    print(html[script_pos+5000:script_pos+7000])
    print('...')
    print(html[script_pos+7000:script_pos+9000])
