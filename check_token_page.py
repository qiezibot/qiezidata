import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    return json.loads(ws.recv())

# Check current page
r = cdp('Runtime.evaluate', {'expression': 'document.title'})
print('Title:', r.get('result', {}).get('result', {}).get('value', 'N/A'))

# Check URL
r = cdp('Runtime.evaluate', {'expression': 'window.location.href'})
print('URL:', r.get('result', {}).get('result', {}).get('value', 'N/A'))

# Get page content to see what's on the screen
r = cdp('Runtime.evaluate', {'expression': 'document.body.innerText.substring(0, 3000)'})
text = r.get('result', {}).get('result', {}).get('value', '')
print('Page text:', text[:2000])

ws.close()
