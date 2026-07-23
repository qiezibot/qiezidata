import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# _ADMIN 模板范围
idx = content.find('_ADMIN = """\\')
tmpl_start = idx + 14  # _ADMIN = """\
tmpl_end = content.find('"""', tmpl_start)
print('Template:', tmpl_start, 'to', tmpl_end)

tmpl = content[tmpl_start:tmpl_end]

# 找到 CSS 开始的位置
css_start = tmpl.find('\npadding:0;box-sizing:border-box}')
print('CSS starts at:', css_start)

# 找到 script 开始
sc1 = tmpl.find('<script>')
print('Script 1 at:', sc1)

# CSS 前面的部分是 JS，后面的部分是 CSS
js_part = tmpl[sc1:css_start]  # 从 <script> 到 CSS 前
css_part = tmpl[css_start:]    # CSS + 后续的内容

# 在 CSS 后面找 </script>（目前没有，但我们要加）
# CSS 后面是 CSS 内容和第二个脚本的内容
# 需要把 CSS 放进 <style> 标签

# 修复方案：在 CSS 前插入 </script><style>，在末尾插入 </style>
new_tmpl = tmpl[:sc1]  # 模板开头到第一个 <script>
new_tmpl += js_part    # 所有 JS 代码（含 <script>开始标签）
new_tmpl += '\n</script>\n<style>\n'  # 关闭 script 开 style
new_tmpl += css_part   # CSS 内容
new_tmpl += '\n</style>'  # 关闭 style

# 验证
sc_count = new_tmpl.count('<script>')
se_count = new_tmpl.count('</script>')
st_count = new_tmpl.count('<style>')
print('After fix - script:', sc_count, '/', se_count, 'style:', st_count)
print('CSS in script:', 'padding:0;box-sizing' in (new_tmpl.split('<script>')[1].split('</script>')[0] if '</script>' in new_tmpl.split('<script>')[1] else ''))

# 只有在新结构正确时才写入
if sc_count == se_count and st_count >= 1:
    new_content = content[:tmpl_start] + new_tmpl + content[tmpl_end:]
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Written OK')
else:
    print('Mismatch - aborting')
