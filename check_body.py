with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)
tmpl = content[tmpl_start:tmpl_end]

# 检查 CSS 中是否包含 script 标签
print('CSS script count:', tmpl.count('<script>', 0, tmpl.find('</head>')))

# 检查 body_start 到 body_end 之间
body_start = tmpl.find('<body>')
body_end = tmpl.find('</body>')
body_content = tmpl[body_start+6:body_end]
print('Body script tags:', body_content.count('<script>'), 'style tags:', body_content.count('<style>'))

# 看看 body 到底有什么
first_sc_in_body = body_content.find('<script>')
if first_sc_in_body >= 0:
    print('Script in body at offset:', first_sc_in_body)
    print('Context:', repr(body_content[first_sc_in_body-20:first_sc_in_body+40]))
