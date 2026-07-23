import sys, re
sys.stdout.reconfigure(encoding='utf-8')

c = open('railway_file_server.py', encoding='utf-8').read()
m = re.search(r'_ADMIN\s*=\s*"""', c)
start = m.end()
end_m = re.search(r'\n"""', c[start:])
end = start + end_m.start()
html = c[start:end]

old_render = "h+='<tr><td>'+u.id+'</td><td>'+u.username+'</td><td>'+(u.display_name||'-')+'</td><td>'+u.role+'</td><td>'+(u.created_at||'')+'</td>'+'<td>'+(u.role==='admin'?'<span style=\"color:green\">\u5df2\u662f\u7ba1\u7406\u5458</span>':'<button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"del-btn\">\u5220\u9664</button><button data-uid=\"'+u.id+'\" data-uname=\"'+u.username+'\" class=\"set-admin-btn\" style=\"margin-left:5px\">\u8bbe\u4e3a\u7ba1\u7406\u5458</button>')+'</td></tr>'"

pos = html.find(old_render)
if pos < 0:
    print('old_render NOT FOUND! Checking differences...')
    # Try the first few chars
    snippet = "h+='<tr><td>'+u.id+'</td>"
    pos2 = html.find(snippet)
    if pos2 >= 0:
        print(f'Found starting part at {pos2}')
        print(repr(html[pos2:pos2+len(snippet)+10]))
else:
    print(f'Found at {pos}')
