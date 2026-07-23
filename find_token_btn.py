import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    return json.loads(ws.recv())

js = '''
let items = [];
document.querySelectorAll('a, button, summary').forEach(function(el) {
  if (el.textContent.toLowerCase().includes('token') || 
      el.textContent.toLowerCase().includes('generate') || 
      el.textContent.toLowerCase().includes('new') ||
      el.textContent.toLowerCase().includes('create')) {
    items.push(el.tagName + ': "' + el.textContent.trim().substring(0,80) + '" href="' + (el.href || '') + '"></a>');
  }
});
items.join('\\n')
'''
r = cdp('Runtime.evaluate', {'expression': js})
v = r.get('result',{}).get('result',{}).get('value','')
print(v)

ws.close()
