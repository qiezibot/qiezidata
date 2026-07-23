c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# 1. exportCD confirm (first occurrence = admin page)
old_export = "async function exportCD(mode){try{var r=await fetch('/clouddata/export/'+mode,{credentials:'include'});if(r.status===401){window.location.href='/';return}var blob=await r.blob();var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='clouddata_'+mode+'_'+new Date().toISOString().slice(0,10)+'.csv';a.click()}catch(e){showToast('\u5bfc\u51fa\u5931\u8d25','error')}}"
new_export = "async function exportCD(mode){var m={all:'\u5168\u90e8',read:'\u5df2\u8bfb',unread:'\u672a\u8bfb'};if(!confirm('\u786e\u5b9a\u5bfc\u51fa'+m[mode]+'?'))return;try{var r=await fetch('/clouddata/export/'+mode,{credentials:'include'});if(r.status===401){window.location.href='/';return}var blob=await r.blob();var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='clouddata_'+mode+'_'+new Date().toISOString().slice(0,10)+'.csv';a.click()}catch(e){showToast('\u5bfc\u51fa\u5931\u8d25','error')}}"

c = c.replace(old_export, new_export)
print('1. exportCD confirm added (both occurrences)')

# 2. markCD confirm (single occurrence)
old_mark = "async function markCD(id,readVal){try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}"
new_mark = "async function markCD(id,readVal){var t=readVal==true?'\u5df2\u8bfb':'\u672a\u8bfb';if(!confirm('\u786e\u5b9a\u6807\u8bb0\u4e3a'+t+'?'))return;try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}"

assert old_mark in c, 'markCD not found!'
c = c.replace(old_mark, new_mark)
print('2. markCD confirm added')

# 3. Add addCloudData function before delCloudData
del_idx = c.find('async function delCloudData')
add_fn = """
async function addCloudData(){var k=document.getElementById('cdKey').value.trim();var v=document.getElementById('cdVal').value.trim();if(!k||!v)return;if(!confirm('\u786e\u5b9a\u6dfb\u52a0 Key='+k+'?'))return;try{var r=await fetch('/admin/clouddata/add',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'include',body:JSON.stringify({key:k,value:v})});if(r.ok){document.getElementById('cdKey').value='';document.getElementById('cdVal').value='';loadCloudData();showToast('\u6dfb\u52a0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
"""
c = c[:del_idx] + add_fn + c[del_idx:]

# Also add addCloudData to the user page (second delFile)
# Let's find the user page's delFile and insert before it
i_user = c.rfind('async function delFile')
c = c[:i_user] + add_fn + c[i_user:]

print('3. addCloudData function inserted (both admin + user pages)')

open('railway_file_server.py', 'w', encoding='utf-8').write(c)

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('ALL OK, size:', len(c))
