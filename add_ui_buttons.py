content = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find the clouddata section
cd_start = content.find('page-clouddata')
old_end = content.find('</div>', cd_start)
old_end = content.find('</div>', old_end + 6)  # close card
old_end = content.find('</div>', old_end + 6)  # close page-clouddata

# The section we want to replace
old_section = content[cd_start:old_end]
print('=== OLD SECTION ===')
print(old_section[:200])

# Build new section with export buttons + mark buttons in table
new_section = '''page-clouddata">
<div class="card"><h2>\u2601 \u4e91\u6570\u636e</h2>
<div style="display:flex;gap:8px;margin-bottom:16px">
<input type="text" id="cdKey" placeholder="Key" style="flex:1;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">
<input type="text" id="cdVal" placeholder="Value" style="flex:2;padding:8px 12px;border:2px solid #eee;border-radius:6px;font-size:14px;outline:none">
<button onclick="addCloudData()" style="padding:8px 20px;background:#667eea;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">\u6dfb\u52a0</button>
</div>
<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
<button onclick="exportCD('all')" style="padding:6px 14px;background:#27ae60;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px">\u2b07 \u5bfc\u51fa\u5168\u90e8</button>
<button onclick="exportCD('read')" style="padding:6px 14px;background:#2980b9;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px">\u2b07 \u5bfc\u51fa\u5df2\u8bfb</button>
<button onclick="exportCD('unread')" style="padding:6px 14px;background:#e67e22;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px">\u2b07 \u5bfc\u51fa\u672a\u8bfb</button>
</div>
<div id="cdList"><p style="color:#999;text-align:center;padding:20px">\u52a0\u8f7d\u4e2d...</p></div>
</div>
</div>'''

content = content[:cd_start] + new_section + content[old_end:]

# Now add the exportCD JS function and update loadCloudData to have mark buttons
# Find the script section
js_marker = 'async function loadCloudData()'
js_idx = content.find(js_marker)

# Insert exportCD function before loadCloudData
export_js = '''
async function exportCD(mode) {
  try{var r=await fetch('/clouddata/export/'+mode,{credentials:'include'});
  if(r.status===401){window.location.href='/';return}
  var blob=await r.blob();var a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='clouddata_'+mode+'_'+new Date().toISOString().slice(0,10)+'.csv';a.click()
  }catch(e){showToast('\u5bfc\u51fa\u5931\u8d25','error')}
}
'''

# Find loadCloudData and add exportJS before it
content = content[:js_idx] + export_js + content[js_idx:]

# Now update loadCloudData to add mark buttons and read status
old_func = '''async function loadCloudData(){try{var r=await fetch('/admin/clouddata',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();if(!d.length){document.getElementById('cdList').innerHTML='<p style=\\"color:#999;text-align:center;padding:20px\\">\\u6682\\u65e0\\u6570\\u636e</p>';return}var h='<table class=\\"user-table\\"><thead><tr><th>Key</th><th>Value</th><th>\\u65f6\\u95f4</th><th>\\u64cd\\u4f5c</th></tr></thead><tbody>';for(var i=0;i<d.length;i++){h+='<tr><td>'+d[i].k+'</td><td>'+d[i].v+'</td><td>'+(d[i].t||'-')+'</td><td><button onclick=\\"delCloudData('+d[i].id+')\\" style=\\"padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px\\">\\u5220\\u9664</button></td></tr>'}h+='</tbody></table>';document.getElementById('cdList').innerHTML=h}catch(e){}}'''

new_func = '''async function loadCloudData(){try{var r=await fetch('/admin/clouddata',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();if(!d.length){document.getElementById('cdList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">\\u6682\\u65e0\\u6570\\u636e</p>';return}var h='<table class=\"user-table\"><thead><tr><th>Key</th><th>Value</th><th>\\u65f6\\u95f4</th><th>\\u72b6\\u6001</th><th>\\u64cd\\u4f5c</th></tr></thead><tbody>';for(var i=0;i<d.length;i++){var rs=d[i].read?'\\u5df2\\u8bfb':'\\u672a\\u8bfb';var rc=rs==='\\u5df2\\u8bfb'?'#27ae60':'#e67e22';h+='<tr><td>'+d[i].k+'</td><td>'+d[i].v+'</td><td>'+(d[i].t||'-')+'</td><td><span style=\"color:'+rc+';font-weight:500\">'+rs+'</span></td><td><button onclick=\"markCD('+d[i].id+','+(!d[i].read)+')\" style=\"padding:2px 8px;border:1px solid #2980b9;border-radius:4px;color:#2980b9;background:#fff;cursor:pointer;font-size:12px\">'+(d[i].read?'\\u6807\\u672a\\u8bfb':'\\u6807\\u5df2\\u8bfb')+'</button> <button onclick=\"delCloudData('+d[i].id+')\" style=\"padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px\">\\u5220\\u9664</button></td></tr>'}h+='</tbody></table>';document.getElementById('cdList').innerHTML=h}catch(e){}}'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print('Replaced loadCloudData OK')
else:
    print('FAIL: old loadCloudData not found')
    # Find the actual function
    idx2 = content.find('async function loadCloudData')
    print(repr(content[idx2:idx2+500]))

# Add markCD function after delCloudData
del_fn_marker = 'async function delCloudData'
del_idx = content.find(del_fn_marker, content.find('page-clouddata'))

mark_js = '''
async function markCD(id,readVal){try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\\u66f4\\u65b0\\u6210\\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
'''

content = content[:del_idx] + mark_js + content[del_idx:]

open('railway_file_server.py', 'w', encoding='utf-8').write(content)
print('Written OK')

import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('py_compile OK')
print('Size:', len(content))
