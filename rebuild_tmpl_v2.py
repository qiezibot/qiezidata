with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)
tmpl = content[tmpl_start:tmpl_end]

# 直接找正确 body 的开始：第一个 <div class="sidebar">
body_actual_start = tmpl.find('<div class="sidebar"')
# 直接找正确 body 的结束：在 script 后面的 </body>
# 从末尾反向找 </body>
body_real_end = tmpl.rfind('</body>')

# 看从 body_actual_start 到第一个 <script> 之间（纯 HTML）
first_sc = tmpl.find('<script>')
body_html_pure = tmpl[body_actual_start:first_sc]
print('Pure body HTML length:', len(body_html_pure))
print('First 100:', repr(body_html_pure[:100]))
print('Last 100:', repr(body_html_pure[-100:]))

# 找 JS（从第一个 <script> 到第一个 </script>）
first_sc_end = tmpl.find('</script>', first_sc)
js_pure = tmpl[first_sc+8:first_sc_end]
print('\nJS length:', len(js_pure))

# 检查 JS 是否有 CSS
css_in_js = js_pure.find('padding:0;box-sizing')
if css_in_js >= 0:
    print('CSS in JS at', css_in_js)
    js_pure = js_pure[:css_in_js].rstrip('\n;')
    print('Trimmed JS length:', len(js_pure))

# 重建
new_tmpl = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>\u7ba1\u7406\u540e\u53f0 - \u8304\u5b50\u6570\u636e</title></head><body>\n'
new_tmpl += body_html_pure
new_tmpl += '\n<script>\n' + js_pure.strip() + '\n</script>\n'
new_tmpl += '</body></html>'

# 验证
sc = new_tmpl.count('<script>')
se = new_tmpl.count('</script>')
st = new_tmpl.count('<style>')
print(f'\nStructure: script={sc}/{se} style={st}')

# 检查 CSS 是否在 style 标签外
css_outside_style = new_tmpl.replace('<style>', '').replace('</style>', '')
if 'padding:0;box-sizing' in css_outside_style[css_outside_style.find('>body<'):]:
    print('CSS outside style!')
else:
    print('CSS properly inside <style> tags')

# 但 CSS 哪去了？原始 body 没有 style！
# 需要从 CSS 中提取 CSS 并插入 head
# 找第一个 style 标签
first_st = tmpl.find('<style>')
first_st_end = tmpl.find('</style>', first_st)
raw_css = tmpl[first_st+7:first_st_end]
raw_css = raw_css.replace('</script><style>', '')
raw_css = raw_css.strip()

# 插入到 head
new_tmpl = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>\u7ba1\u7406\u540e\u53f0 - \u8304\u5b50\u6570\u636e</title><style>\n' + raw_css + '\n</style></head><body>\n'
new_tmpl += body_html_pure
new_tmpl += '\n<script>\n' + js_pure.strip() + '\n</script>\n'
new_tmpl += '</body></html>'

sc = new_tmpl.count('<script>')
se = new_tmpl.count('</script>')
st = new_tmpl.count('<style>')
print(f'\nFinal structure: script={sc}/{se} style={st}')
css_in_script = 'padding:0;box-sizing' in new_tmpl[new_tmpl.find('<script>'):new_tmpl.find('</script>')]
print(f'CSS in script: {css_in_script}')
print(f'Size: {len(new_tmpl)} bytes')

if sc == se == 1 and st == 1 and not css_in_script:
    new_content = content[:tmpl_start] + new_tmpl + content[tmpl_end:]
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('Written OK, py_compile OK')
else:
    print('Structure invalid, not writing')
