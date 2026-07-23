import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    r = json.loads(ws.recv())
    return r.get('result')

# Navigate directly to classic token creation page
cdp('Page.navigate', {'url': 'https://github.com/settings/tokens/new'})

import time
time.sleep(4)

r = cdp('Runtime.evaluate', {'expression': 'window.location.href'})
print('URL:', r.get('result',{}).get('value','N/A'))

r = cdp('Runtime.evaluate', {'expression': 'document.title'})
print('Title:', r.get('result',{}).get('value','N/A'))

# Check what form elements exist
r = cdp('Runtime.evaluate', {'expression': '''
document.querySelector("#token_scope").value
'''})
v = r.get('result',{}).get('value','')
print('Scope textarea:', v[:200] if v else 'NOT FOUND')

# Find the note/name field
r = cdp('Runtime.evaluate', {'expression': '''
Array.from(document.querySelectorAll("input")).filter(function(i){return i.type==="text" || i.type==="search"}).map(function(i){return i.id||i.name||i.placeholder}).join(", ")
'''})
v = r.get('result',{}).get('value','')
print('Text inputs:', v)

ws.close()
