import sys, json, websocket

tab_id = '4222CAE4982630BD21B7D30ACE779241'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    resp = json.loads(ws.recv())
    return resp.get('result')

# Check page title
r = cdp('Runtime.evaluate', {'expression': 'document.title'})
print('Title:', r.get('result', {}).get('value', 'N/A'))

# Check if we see login form
r = cdp('Runtime.evaluate', {'expression': 'document.querySelector("#login_field") !== null'})
print('Has login field:', r.get('result', {}).get('value'))

if r.get('result', {}).get('value'):
    # We need user credentials - ask user
    print("Need GitHub login!")
else:
    # Check the URL
    r = cdp('Runtime.evaluate', {'expression': 'window.location.href'})
    print('URL:', r.get('result', {}).get('value', 'N/A'))

ws.close()
