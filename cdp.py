import sys, json, websocket

tab_id = sys.argv[1]
method = sys.argv[2]
params_str = sys.argv[3] if len(sys.argv) > 3 else '{}'
params = json.loads(params_str)

ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')
ws.send(json.dumps({'id': 1, 'method': method, 'params': params}))
resp = json.loads(ws.recv())
ws.close()

if 'result' in resp:
    print(json.dumps(resp['result'], indent=2, ensure_ascii=False)[:500])
else:
    print(json.dumps(resp, indent=2, ensure_ascii=False)[:500])
