import re
c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# 1. Fix Response import
c = c.replace(
    'from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse',
    'from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse, RedirectResponse, Response'
)
print('1. Response import fixed')

# 2. Fix clouddata_list: already uses db_fetch, just verify
assert 'db_fetch' in c[c.find('def clouddata_list'):c.find('def clouddata_list')+400], 'clouddata_list not using db_fetch!'
print('2. clouddata_list already uses db_fetch OK')

# 3. Add export buttons + markCD function + update loadCloudData
# Find clouddata card section
cd_start = c.find('page-clouddata">')
old_end = c.find('</div>', cd_start)
old_end = c.find('</div>', old_end + 6)
old_end = c.find('</div>', old_end + 6)

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

c = c[:cd_start] + new_section + c[old_end:]
print('3. Clouddata UI with export buttons added')

# 4. Update loadCloudData to include mark/status columns
old_lcd = c[c.find('async function loadCloudData'):]
old_lcd = old_lcd[:old_lcd.find('async function delCloudData')]

new_lcd = '''async function loadCloudData(){try{var r=await fetch('/admin/clouddata',{credentials:'include'});if(r.status===401){window.location.href='/';return}var d=await r.json();if(!d.length){document.getElementById('cdList').innerHTML='<p style=\\"color:#999;text-align:center;padding:20px\\">\u6682\u65e0\u6570\u636e</p>';return}var h='<table class=\\"user-table\\"><thead><tr><th>Key</th><th>Value</th><th>\u65f6\u95f4</th><th>\u72b6\u6001</th><th>\u64cd\u4f5c</th></tr></thead><tbody>';for(var i=0;i<d.length;i++){var rs=d[i].read?'\u5df2\u8bfb':'\u672a\u8bfb';var rc=rs=='\u5df2\u8bfb'?'#27ae60':'#e67e22';h+='<tr><td>'+d[i].k+'</td><td>'+d[i].v+'</td><td>'+(d[i].t||'-')+'</td><td><span style=\\"color:'+rc+';font-weight:500\\">'+rs+'</span></td><td><button onclick=\\"markCD('+d[i].id+','+(!d[i].read)+')\\" style=\\"padding:2px 8px;border:1px solid #2980b9;border-radius:4px;color:#2980b9;background:#fff;cursor:pointer;font-size:12px\\">'+(d[i].read?'\u6807\u672a\u8bfb':'\u6807\u5df2\u8bfb')+'</button> <button onclick=\\"delCloudData('+d[i].id+')\\" style=\\"padding:2px 8px;border:1px solid #e74c3c;border-radius:4px;color:#e74c3c;background:#fff;cursor:pointer;font-size:12px\\">\u5220\u9664</button></td></tr>'}h+='</tbody></table>';document.getElementById('cdList').innerHTML=h}catch(e){}}
'''

assert old_lcd in c, 'old loadCloudData not found!'
c = c.replace(old_lcd, new_lcd)
print('4. loadCloudData updated with mark/status')

# 5. Add exportCD function before loadCloudData
js_marker = 'async function loadCloudData'
js_idx = c.find(js_marker)
export_js = '''
async function exportCD(mode){try{var r=await fetch('/clouddata/export/'+mode,{credentials:'include'});if(r.status===401){window.location.href='/';return}var blob=await r.blob();var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='clouddata_'+mode+'_'+new Date().toISOString().slice(0,10)+'.csv';a.click()}catch(e){showToast('\u5bfc\u51fa\u5931\u8d25','error')}}
'''
c = c[:js_idx] + export_js + c[js_idx:]

# 6. Add markCD function before delCloudData
del_marker = 'async function delCloudData'
del_idx = c.find(del_marker, c.find('page-clouddata'))
mark_js = '''
async function markCD(id,readVal){try{var r=await fetch('/clouddata/mark/id/'+id+'?read='+readVal,{method:'POST',credentials:'include'});if(r.ok){loadCloudData();showToast('\u66f4\u65b0\u6210\u529f','success')}else if(r.status===401)window.location.href='/'}catch(e){}}
'''
c = c[:del_idx] + mark_js + c[del_idx:]
print('5-6. exportCD + markCD functions inserted')

# 7. Add Response import check
assert ', Response' in c, 'Response import lost!'

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)

# Final verification
print()
print('=== FINAL VERIFICATION ===')
checks = ['function exportCD','function markCD','function delCloudData','function addCloudData',
          'Response,','db_fetch(','\u5bfc\u51fa\u5168\u90e8','\u5bfc\u51fa\u5df2\u8bfb','\u5bfc\u51fa\u672a\u8bfb',
          '\u6807\u5df2\u8bfb','\u6807\u672a\u8bfb','\u72b6\u6001']
all_ok = True
for ch in checks:
    ok = ch in c
    if not ok:
        all_ok = False
        if not ok: print(f'  MISSING: {ch}')
print(f'  Size: {len(c)} bytes')
print(f'  ALL OK: {all_ok}')
