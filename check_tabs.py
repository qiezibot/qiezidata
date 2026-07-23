import sys, json, websocket

def cdp_send(ws, cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    return json.loads(ws.recv())

ws = websocket.create_connection('ws://localhost:9222/devtools/page/4222CAE4982630BD21B7D30ACE779241')

# Get all tabs
import urllib.request, json as j
tabs = j.loads(urllib.request.urlopen('http://localhost:9222/json').read())
for t in tabs:
    url = t.get('url', '')
    print(t['id'][:20] + ' | ' + url[:100])
    if 'github.com/settings/tokens' in url:
        print(">>> FOUND settings/tokens tab!")
        # Navigate to this tab
        ws2 = websocket.create_connection(f'ws://localhost:9222/devtools/page/{t["id"]}')
        r = cdp_send(ws2, 'Runtime.evaluate', {'expression': 'document.title'})
        print('Title:', r.get('result', {}).get('result', {}).get('value', 'N/A'))
        ws2.close()

ws.close()
