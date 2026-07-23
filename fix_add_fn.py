c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find the admin page's script area: the last '</script>' before _USER template
admin_script_end = c.find('loadDashboard()</script>')

add_code = '''async function addCloudData(){var k=document.getElementById("cdKey").value.trim();var v=document.getElementById("cdVal").value.trim();if(!k||!v)return;if(!confirm("\u786e\u5b9a\u6dfb\u52a0 Key="+k+"?"))return;try{var r=await fetch("/admin/clouddata/add",{method:"POST",headers:{"Content-Type":"application/json"},credentials:"include",body:JSON.stringify({key:k,value:v})});if(r.ok){document.getElementById("cdKey").value="";document.getElementById("cdVal").value="";loadCloudData();showToast("\u6dfb\u52a0\u6210\u529f","success")}else if(r.status===401)window.location.href="/"}catch(e){}}\n'''

c = c[:admin_script_end] + add_code + c[admin_script_end:]
print('addCloudData inserted into ADMIN template')

# Also fix exportCD in admin template - only add confirm to admin one
# Need to find the specific exportCD in admin script vs user script
# Admin exportCD is before loadCloudData, user page doesn't have clouddata
print('Confirm check:')
import re
for m in re.finditer(r'async function exportCD', c):
    print('  exportCD at', m.start(), 'ctx:', c[m.start():m.start()+30])

# The admin template has its own issues: exportCD confirm was added to both templates
# Let's verify
print()
print('Total addCloudData refs:', sum(1 for _ in re.finditer(r'addCloudData', c)))
print('Last 200 bytes of file:', repr(c[-200:]))

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK size:', len(c))
