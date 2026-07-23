content = open('railway_file_server.py', 'r', encoding='utf-8').read()

old_func = content[content.find('async function loadCloudData'):]
old_func = old_func[:old_func.find('async function delCloudData')]

# Build new loadCloudData that includes mark/unmark buttons
new_func = '''async function loadCloudData(){try{var r=await fetch('/admin/clouddata',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();if(!d.length){document.getElementById('cdList').innerHTML='<p style=\"color:#999;text-align:center;padding:20px\">\u6682\u65e0\u6570\u636e</p>';return}var h='<table class=\"user-table\"><thead><tr><th>Key</th><th>Value</th><th>\u65f6\u95f4</th><th>\u72b6\u6001</th><th>\u64cd\u4f5c</th></tr></thead><tbody>';for(var i=0;i<d.length;i++){var rs=d[i].read?'\u5df2\u8bfb':'\u672a\u8bfb';var rc=rs=='\u5df2\u8bfb'?'#27ae60':'#e67e22';h+='<tr><td>'+d[i].k+'</td><td>'+d[i].v+'</td><td>'+(d[i].t||'-')+'</td><td><span style=\"color:'+rc+';font-weight:500\">'+rs+'</span></td><td><button onclick=\"markCD('+d[i].id+','+(!d[i].read)+')\" style=\"padding:2px 8px;border:1px solid #2980b9;border-radius:4px;color:#2980b9;background:#fff;cursor:pointer;font-size:12px\">'+(d[i].read?'\u6807\u672a\u8bfb':'\u6807\u5df2\u8bfb')+'</button> <button onclick=\"delCloudData('+d[i].id+')\" style=\"padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px\">\u5220\u9664</button></td></tr>'}h+='</tbody></table>';document.getElementById('cdList').innerHTML=h}catch(e){}}
'''

content = content.replace(old_func, new_func)

open('railway_file_server.py', 'w', encoding='utf-8').write(content)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK Size:', len(content))
