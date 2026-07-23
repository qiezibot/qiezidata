with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# _ADMIN 模板
idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)

tmpl = content[tmpl_start:tmpl_end]

# 提取 CSS: 第一个 <style> 到 </style> 之间的内容  
st_start = tmpl.find('<style>')
st_end = tmpl.find('</style>', st_start)
if st_end > 0:
    css_content = tmpl[st_start+7:st_end]

# 提取 JS: 第一个 <script> 之间的内容
# 找到真正的 JS（从第一个 <script> 到 CSS 开始之间）
sc_start = tmpl.find('<script>')
print('Style:', st_start, '-', st_end)
print('Script:', sc_start)

# CSS 正确内容应该在第一个 <style> 里（154-3826）
# 从第一个 <style> 到第一个 </style> 之间
first_style = tmpl.find('<style>')
first_style_end = tmpl.find('</style>', first_style)
print('First style:', first_style, 'to', first_style_end)
print('First style content:')
print(tmpl[first_style+7:first_style_end][:200])
print('...')
print(tmpl[first_style_end-50:first_style_end])

# 第二个 style（被错误插入的）
second_style = tmpl.find('<style>', first_style_end)
print('\nSecond style at:', second_style)
if second_style > 0:
    second_style_end = tmpl.find('</style>', second_style)
    print('Second style end:', second_style_end)
    print('Second style content:', tmpl[second_style+7:second_style_end][:200])
    
# 第三个 style
third_style = tmpl.find('<style>', second_style+1) if second_style > 0 else -1
if third_style > 0:
    third_style_end = tmpl.find('</style>', third_style)
    print('\nThird style at:', third_style, 'end:', third_style_end)
    print('Content:', tmpl[third_style+7:third_style_end][:200])
