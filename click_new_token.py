import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    r = json.loads(ws.recv())
    return r.get('result')

# Click "Generate new token (classic)"
js = '''
(function() {
  let links = document.querySelectorAll('a');
  for (let a of links) {
    if (a.href && a.href.includes('tokens/new')) {
      a.click();
      return 'Clicked!';
    }
  }
  return 'Not found';
})()
'''
r = cdp('Runtime.evaluate', {'expression': js})
print('Result:', r.get('result',{}).get('value','N/A'))

# Wait and check URL
import time
time.sleep(3)
r = cdp('Runtime.evaluate', {'expression': 'window.location.href'})
print('New URL:', r.get('result',{}).get('value','N/A'))

ws.close()
