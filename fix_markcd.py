c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find the place to insert markCD function - after delCloudData function
insert_marker = 'async function delCloudData'
idx = c.find(insert_marker)
if idx < 0:
    print('ERROR: delCloudData not found')
else:
    # Find where the function ends (next function or other marker)
    after_fn = c.find('\n}', idx)
    after_fn = c.find('\n', after_fn + 3)  # next line
    
    mark_js = '''
async function markCD(id,readVal){try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
'''
    c = c[:after_fn] + mark_js + c[after_fn:]
    open('railway_file_server.py', 'w', encoding='utf-8').write(c)
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('markCD inserted OK at', after_fn)
    print('Size:', len(c))
