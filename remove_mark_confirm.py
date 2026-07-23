c = open('railway_file_server.py', 'r', encoding='utf-8').read()

old_mark = "async function markCD(id,readVal){var t=readVal==true?'\u5df2\u8bfb':'\u672a\u8bfb';if(!confirm('\u786e\u5b9a\u6807\u8bb0\u4e3a'+t+'?'))return;try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}"
new_mark = "async function markCD(id,readVal){try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}"

assert old_mark in c, 'markCD not found!'
c = c.replace(old_mark, new_mark)
open('railway_file_server.py', 'w', encoding='utf-8').write(c)

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('markCD confirm removed, size:', len(c))
