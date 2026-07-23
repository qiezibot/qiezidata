import re

with open('railway_file_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到问题代码
idx = content.find("if(confirm('确定删除?'))deleteCD")
if idx >= 0:
    print('Found at:', idx)
    
    # 修复: 把 '确定删除?' 改成 "确定删除?"
    old = "if(confirm('确定删除?'))deleteCD"
    new = 'if(confirm("确定删除?"))deleteCD'
    content = content.replace(old, new)
    
    # 检查 _ADMIN 模板中的其他类似模式
    admin_idx = content.find('_ADMIN = ')
    if admin_idx > 0:
        tmpl = content[admin_idx:]
        # 找 onclick 中嵌套单引号的问题
        # 搜索 onclick="if(confirm(' 模式
        for m in re.finditer(r"onclick=\"[^\"]*confirm\('[^']*'\)[^\"]*\"", tmpl):
            print('Found nested quote:', m.group()[:100])
    
    with open('railway_file_server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('py_compile OK')
else:
    print('Pattern not found')
