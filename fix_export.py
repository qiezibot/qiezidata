c = open('railway_file_server.py','r',encoding='utf-8').read()
old_export = 'async function exportCD(mode){var m={all:\"\u5168\u90e8\",read:\"\u5df2\u8bfb\",unread:\"\u672a\u8bfb\"};if(!confirm(\"\u786e\u5b9a\u5bfc\u51fa\"+m[mode]+\"?\"))return;try{var r=await fetch(\"/clouddata/export/\"+mode,{credentials:\"include\"});if(r.status===401){window.location.href=\"/\";return}var blob=await r.blob();var a=document.createElement(\"a\");a.href=URL.createObjectURL(blob);a.download=\"clouddata_\"+mode+\"_\"+new Date().toISOString().slice(0,10)+\".csv\";a.click()}catch(e){showToast(\"\u5bfc\u51fa\u5931\u8d25\",\"error\")}}'
new_export = 'function exportCD(mode){var pid=document.getElementById(\"cdpSelect\").value;var m={all:\"\u5168\u90e8\",read:\"\u5df2\u8bfb\u53d6\",unread:\"\u672a\u8bfb\u53d6\"};if(!confirm(\"\u786e\u5b9a\u5bfc\u51fa\"+m[mode]+\"?\"))return;window.open(\"/admin/cddata/export/\"+pid+\"/\"+mode)}'
if old_export not in c:
    print('Old exportCD not found! Searching...')
    i = c.find('function exportCD')
    print('Found at', i, ':', c[i:i+150])
else:
    c = c.replace(old_export, new_export)
    open('railway_file_server.py','w',encoding='utf-8').write(c)
    import py_compile
    py_compile.compile('railway_file_server.py', doraise=True)
    print('exportCD updated, size:', len(c))
