import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    r = json.loads(ws.recv())
    return r.get('result')

# Fill in token name
cdp('Runtime.evaluate', {'expression': '''
document.querySelector("#oauth_access_description").value = "railway deploy";
document.querySelector("#oauth_access_description").dispatchEvent(new Event("input", {bubbles: true}));
''', 'returnByValue': True})

import time
time.sleep(1)

# Check if repo scope checkbox exists
r = cdp('Runtime.evaluate', {'expression': '''
let scopes = Array.from(document.querySelectorAll("input[type=checkbox]"));
scopes.map(function(c){return c.id + "=" + c.checked}).join(", ")
'''})
v = r.get('result',{}).get('value','')
print('Checkboxes:', v[:1000])

# Try to find and check repo scope
r = cdp('Runtime.evaluate', {'expression': '''(function(){
let scopes = document.querySelectorAll("input[type=checkbox]");
for(let c of scopes) {
  if(c.id === "repo" || c.value === "repo") { c.checked=true; return "repo checked!"; }
  if(c.name === "scope" && c.value === "repo") { c.checked=true; return "repo checked by name!"; }
}
return "repo checkbox not found. ids: " + Array.from(scopes).map(s=>s.id).join(", ");
})()'''})
v = r.get('result',{}).get('value','')
print('Repo scope:', v)

# Try using scope textarea
r = cdp('Runtime.evaluate', {'expression': '''
let ta = document.querySelector("#token_scope");
if(!ta) return "no textarea";
ta.value = "repo";
ta.dispatchEvent(new Event("input", {bubbles:true}));
return "done, value=" + ta.value;
'''})
v = r.get('result',{}).get('value','')
print('Textarea:', v)

ws.close()
