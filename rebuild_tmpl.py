with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14
tmpl_end = content.find('"""', tmpl_start)
tmpl = content[tmpl_start:tmpl_end]

# === 提取正确的 CSS ===
# 找第一个 <style> 标签内的所有内容，直到第一个 </style>
first_st = tmpl.find('<style>')
first_st_end = tmpl.find('</style>', first_st)
# 但第一个 <style> 里有被注入的 </script><style> 需要清理
raw_css1 = tmpl[first_st+7:first_st_end]
css_clean = raw_css1.replace('</script><style>', '')
# 检查是否还有残留
print('CSS1 length:', len(raw_css1), '-> cleaned:', len(css_clean))

# 还有第二个 <style> 完整副本，但也混入了一些
second_st = tmpl.find('<style>', 182)
if second_st > 0:
    second_st_end = tmpl.find('</style>', second_st)
    raw_css2 = tmpl[second_st+7:second_st_end]
    css_clean2 = raw_css2.replace('padding:0;box-sizing:border-box}', '*{margin:0;padding:0;box-sizing:border-box}')
    print('CSS2 length:', len(raw_css2))
else:
    css_clean2 = ''

# 用较长的那个 CSS
final_css = css_clean if len(css_clean) > len(css_clean2) else css_clean2
final_css = final_css.strip()
print('Final CSS length:', len(final_css))

# === 提取正确的 JS ===
# 找真正的 JS 内容（从第一个 <script> 到最后一个 </script>）
first_sc = tmpl.find('<script>')
last_sc_end = tmpl.rfind('</script>')
all_js = tmpl[first_sc+8:last_sc_end]

# 去掉 JS 中的 CSS 残留
css_pos = all_js.find('padding:0;box-sizing')
if css_pos > 0:
    all_js = all_js[:css_pos]

# 去掉末尾空行
all_js = all_js.strip()
print('Final JS length:', len(all_js))

# 检查 JS 是否含 script/style 标签
if '<script>' in all_js or '<style>' in all_js:
    # 去掉第二份 script/style
    all_js = all_js.split('<script>')[0]
    if '<style>' in all_js:
        all_js = all_js.split('<style>')[0]
    all_js = all_js.strip()
    print('After strip embedded tags, JS length:', len(all_js))

# === 提取正确的 body HTML ===
body_start = tmpl.find('<body>')
body_end = tmpl.find('</body>')
# body 里的内容（不含 <body> 和 </body> 标签本身）
# 从 body 开始到第一个 <script> 之间是 body HTML
# 从 </script> 到 </body> 是 body HTML 后半部分
body_html_start = tmpl[body_start+6:first_sc]
# 从最后一个 </script> 到 </body>
body_html_end = tmpl[last_sc_end+9:body_end]

# 合并 body HTML
body_html = body_html_start.strip() + '\n' + body_html_end.strip()
print('Body HTML length:', len(body_html))

# === 重建模板 ===
new_tmpl = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>\u7ba1\u7406\u540e\u53f0 - \u8304\u5b50\u6570\u636e</title>'
new_tmpl += '<style>\n' + final_css + '\n</style>'
new_tmpl += '</head><body>\n' + body_html
new_tmpl += '\n<script>\n' + all_js + '\n</script>\n'
new_tmpl += '</body></html>'

# 验证结构
sc_ct = new_tmpl.count('<script>')
se_ct = new_tmpl.count('</script>')
st_ct = new_tmpl.count('<style>')
print(f'\nStructure: script={sc_ct}/{se_ct} style={st_ct}')
assert sc_ct == se_ct == 1, f'Script mismatch: {sc_ct} open / {se_ct} close'
assert st_ct == 1, f'Style count: {st_ct}'
assert 'padding:0;box-sizing' not in new_tmpl[new_tmpl.find('<script>'):new_tmpl.find('</script>')], 'CSS in script!'

# 写入
new_content = content[:tmpl_start] + new_tmpl + content[tmpl_end:]
with open('railway_file_server.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('py_compile OK')
print('New template size:', len(new_tmpl), 'bytes')
