with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 _ADMIN 模板
idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)
tmpl = content[tmpl_start:tmpl_end]

# === 识别正确的内容区域 ===

# 正确的 CSS 应该在第一个 <style> 和最后一个 </style> 之间
# 第一个 style 
first_st = tmpl.find('<style>')
first_st_end = tmpl.find('</style>', first_st)
# 最后一个 style
last_st_end = tmpl.rfind('</style>')

# 第一个 <script>
first_sc = tmpl.find('<script>')
# 应该在最后一个 </style> 之后 (> 9554 已经有了)
# 最后一个 </script>
last_sc = tmpl.rfind('</script>')

print('First style:', first_st, '-', first_st_end)
print('Last style end:', last_st_end)
print('First script:', first_sc)
print('Last script:', last_sc)

# 提取真正的 CSS（从 <style> 之后到最后一个 </style>）
# 但要去掉中间被插入的 </script><style>
raw_css_area = tmpl[first_st+7:last_st_end]
# 去掉 </script> 和 <style> 标签
raw_css_area = raw_css_area.replace('</script>', '')
raw_css_area = raw_css_area.replace('<style>', '')

# 现在 raw_css_area 是纯 CSS

# 提取 JS（从 <script> 到 </script>）
raw_js_area = tmpl[first_sc+8:last_sc]
# JS 应该不包含 CSS，但可能被之前的修复切断了
# 去掉 JS 后面的 CSS 残留
css_idx_in_js = raw_js_area.find('padding:0;box-sizing')
if css_idx_in_js > 0:
    raw_js_area = raw_js_area[:css_idx_in_js]
    # 去掉末尾可能不完整的语句
    raw_js_area = raw_js_area.rstrip('\n;')

# 模板开始到 <style> 之间的部分
head_part = tmpl[:first_st]

# 模板在 </script> 之后的部分
after_js = tmpl[last_sc+9:]

# 重建干净模板
new_tmpl = head_part
new_tmpl += '<style>\n'
new_tmpl += raw_css_area.strip()
new_tmpl += '\n</style>\n'
new_tmpl += '</head><body>\n'
# 把 body 内容放在 script 之前（正常的 HTML 结构）
# 从原来的 body 内容提取（在 js 之前）
# 实际上 after_js 之后就是 body 内容

# 现在先包含 body HTML（介于 </style> 和 <script> 之间）
# 从 last_st_end 到 first_sc 之间的内容就是 body HTML
body_html = tmpl[last_st_end+7:first_sc]  # +7 for </style>
# 去掉可能残留的 </script>
body_html = body_html.replace('</script>', '')

new_tmpl += body_html.strip()
new_tmpl += '\n<script>\n'
new_tmpl += raw_js_area.strip()
new_tmpl += '\n</script>\n'
new_tmpl += after_js

# 验证
sc_count = new_tmpl.count('<script>')
se_count = new_tmpl.count('</script>')
st_count = new_tmpl.count('<style>')
print('\n=== Verification ===')
print('script:', sc_count, '/', se_count)
print('style:', st_count)
css_in_script = 'padding:0;box-sizing' in new_tmpl[new_tmpl.find('<script>'):new_tmpl.find('</script>')]
print('CSS in script:', css_in_script)
print('Total length:', len(new_tmpl))

if sc_count == se_count and sc_count == 1 and not css_in_script:
    new_content = content[:tmpl_start] + new_tmpl + content[tmpl_end:]
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('\nWritten OK')
    
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('py_compile OK')
else:
    print('\nStructure invalid, not writing')
