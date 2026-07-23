content = open('railway_file_server.py', 'r', encoding='utf-8').read()

# 找到 _ADMIN 模板中 CSS 混入 script 的问题
idx = content.find('_ADMIN = ')
quote_start = content.find("'''", idx)
rest = content[quote_start+3:]

sc_start = rest.find('<script>')
css_in_script = rest.find('padding:0;box-sizing', sc_start)

print('CSS in script at position:', css_in_script)

# 在 CSS 前插入 </script><style>
# 将 CSS 部分从 script 里移出来
before_css = rest[:css_in_script]
# 找到后面的 </script>
orig_end = rest.find('</script>', css_in_script)
css_stuff = rest[css_in_script:orig_end]
after = rest[orig_end+9:]  # +9 for </script>

# 重组
new_rest = before_css + '</script><style>' + css_stuff + '</style>' + after

# 验证
sc_start2 = new_rest.find('<script>')
sc_end2 = new_rest.find('</script>')
st_start2 = new_rest.find('<style>')
st_end2 = new_rest.find('</style>')
print('New script:', sc_start2, '-', sc_end2)
print('New style:', st_start2, '-', st_end2)

css_still_in_script = 'padding:0;box-sizing' in new_rest[sc_start2:sc_end2]
print('CSS still in script tag:', css_still_in_script)

if not css_still_in_script:
    # 写回
    new_content = content[:quote_start+3] + new_rest
    # 找模板结束的三引号
    tmpl_end = new_content.find("'''", quote_start+3)
    print('Template end at:', tmpl_end)
    # 确保模板结束符还在
    open('railway_file_server.py', 'w', encoding='utf-8').write(new_content)
    print('Written OK')
else:
    print('Fix failed!')
