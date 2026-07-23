import sys, json, websocket

tab_id = '16497F6424B07D7514C862B67EB2412D'
ws = websocket.create_connection(f'ws://localhost:9222/devtools/page/{tab_id}')

def cdp(cmd, params=None):
    if params is None: params = {}
    ws.send(json.dumps({'id': 1, 'method': cmd, 'params': params}))
    r = json.loads(ws.recv())
    return r.get('result')

# Click "Generate token" button
r = cdp('Runtime.evaluate', {'expression': '''(function(){
let btns = document.querySelectorAll("button");
for(let b of btns) {
  if(b.textContent.includes("Generate token")) {
    b.click();
    return "Clicked!";
  }
}
return "Not found. Buttons: " + Array.from(btns).map(b=>b.textContent.trim()).filter(t=>t).join(" | ");
})()'''})
print('Click result:', r.get('result',{}).get('value','N/A'))

import time
time.sleep(4)

# Now get the generated token
r = cdp('Runtime.evaluate', {'expression': '''(function(){
// GitHub shows the token in an input
let inputs = document.querySelectorAll("input");
for(let i of inputs) {
  if(i.type === "text" && i.value && i.value.startsWith("ghp_")) return i.value;
}
// Check for code or pre elements
let pres = document.querySelectorAll("code, pre, input");
for(let p of pres) {
  if(p.value && p.value.startsWith("ghp_")) return p.value;
  if(p.textContent && p.textContent.trim().startsWith("ghp_")) return p.textContent.trim();
}
// Maybe still on same page
return "Token not found yet. URL: " + window.location.href;
})()'''})
v = r.get('result',{}).get('value','N/A')
print('Token/generated:', v[:100])

ws.close()
