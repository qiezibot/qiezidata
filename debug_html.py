content = open('railway_file_server.py', 'r', encoding='utf-8').read()
idx = content.find('_ADMIN = ')
if idx > 0:
    admin_end = content.find("'''", idx + 5)
    if admin_end < 0:
        admin_end = content.find('"""', idx + 5)
    print('ADMIN template:', idx, 'to', admin_end)
    sc_start = content.find('<script>', idx)
    sc_end = content.find('</script>', idx) + 9
    st_start = content.find('<style>', idx)
    st_end = content.find('</style>', idx) + 7
    print('Script:', sc_start, '-', sc_end)
    print('Style:', st_start, '-', st_end)
    print('After style tag:', repr(content[st_end:st_end+50]))
    print('Before script tag:', repr(content[sc_start-30:sc_start]))
    print('Script is after style:', sc_start > st_end)
    
    # 看是不是CSS混进了script
    between = content[st_end:sc_start]
    print('\nBetween style end and script start:', len(between), 'chars')
    print(repr(between[:100]))
    
    # 检查 script 内部是否包含 CSS
    script_content = content[sc_start:sc_end]
    css_in_script = script_content.find('padding:0;box-sizing')
    if css_in_script > 0:
        print('\n!!! CSS FOUND IN SCRIPT TAG at offset', css_in_script)
        print(script_content[css_in_script-50:css_in_script+100])
