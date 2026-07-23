with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)
tmpl = content[tmpl_start:tmpl_end]

# 查看完整的标签顺序
import re
for m in re.finditer(r'<(/?)(script|style)[^>]*>', tmpl):
    tag = m.group(0)
    pos = m.start()
    ctx_before = repr(tmpl[max(0,pos-30):pos])
    ctx_after = repr(tmpl[pos+len(tag):pos+len(tag)+30])
    print(f'{pos:>6}: {tag:20} | ...{ctx_before} -> {ctx_after}...')

# 更重要的：查看完整 HTML 结构
print('\n=== Document structure ===')
print(f'Head (<head> to </head>):')
head_start = tmpl.find('<head>')
head_end = tmpl.find('</head>')
print(f'  {head_start} - {head_end}')
body_start = tmpl.find('<body>')
body_end = tmpl.find('</body>')
print(f'Body: {body_start} - {body_end}')
