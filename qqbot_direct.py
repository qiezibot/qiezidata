import asyncio, json, os, sys, struct, time, signal, threading
import urllib.request, urllib.error

APP_ID = "1904006743"
APP_SECRET = "iItV7kO2hM2jQ8qZJ3oaM9wkZOE4vnfY"
TOKEN = f"Bot {APP_ID}.{APP_SECRET}"

ws = None
seq = None
session_id = None
heartbeat_interval = 0
last_heartbeat_ack = time.time()

def get_gateway_url():
    req = urllib.request.Request("https://api.sgroup.qq.com/gateway")
    req.add_header("Authorization", TOKEN)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        print(f"[QQBot] Gateway URL: {data.get('url')}")
        return data.get("url")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[QQBot] HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print(f"[QQBot] Error getting gateway: {e}")
        return None

async def connect():
    global ws, seq, session_id, heartbeat_interval
    
    gateway_url = get_gateway_url()
    if not gateway_url:
        print("[QQBot] Failed to get gateway URL, check AppID/AppSecret")
        return False
    
    import websocket
    try:
        ws = websocket.WebSocket()
        ws.connect(gateway_url, timeout=10)
        print("[QQBot] WebSocket connected")
    except Exception as e:
        print(f"[QQBot] WebSocket connect failed: {e}")
        return False
    
    # Read Hello
    msg = json.loads(ws.recv())
    if msg.get("op") != 10:
        print(f"[QQBot] Expected Hello (op=10), got: {msg.get('op')}")
        return False
    
    heartbeat_interval = msg["d"]["heartbeat_interval"] / 1000.0
    print(f"[QQBot] Heartbeat interval: {heartbeat_interval}s")
    
    # Send Identify
    ws.send(json.dumps({
        "op": 2,
        "d": {
            "token": TOKEN,
            "intents": (1 << 30) | (1 << 25) | (1 << 9) | (1 << 0),
            "shard": [0, 1],
            "properties": {"$os": "windows", "$browser": "openclaw", "$device": "openclaw"}
        }
    }))
    print("[QQBot] Identify sent")
    
    # Wait for Ready
    while True:
        msg = json.loads(ws.recv())
        if msg.get("op") == 0 and msg.get("t") == "READY":
            session_id = msg["d"]["session_id"]
            user = msg["d"].get("user", {})
            print(f"[QQBot] Ready! Bot: {user.get('id')} - {user.get('username')}")
            if msg.get("s"): seq = msg["s"]
            return True
        elif msg.get("op") == 0 and msg.get("s"):
            seq = msg["s"]
        elif msg.get("op") == 11:
            last_heartbeat_ack = time.time()

def heartbeat_thread():
    global ws, seq, last_heartbeat_ack
    while ws and ws.connected:
        time.sleep(heartbeat_interval * 0.8)
        try:
            ws.send(json.dumps({"op": 1, "d": seq}))
        except:
            break

def handle_message(msg):
    global seq
    d = msg.get("d", {})
    t = msg.get("t")
    op = msg.get("op")
    
    if msg.get("s"): seq = msg["s"]
    
    if op == 11:  # Heartbeat ACK
        global last_heartbeat_ack
        last_heartbeat_ack = time.time()
        return
    
    if op == 0 and t == "AT_MESSAGE_CREATE":
        content = d.get("content", "")
        author = d.get("author", {})
        username = author.get("username", "unknown")
        open_id = author.get("id", "")
        channel_id = d.get("channel_id", "")
        print(f"[QQBot] AT from {username}: {content}")
        
        # Reply
        reply_text = f"你好，我是茄子！已收到你的消息。"
        send_msg(channel_id, reply_text, d.get("id"))
    
    elif op == 0 and t == "MESSAGE_CREATE":
        content = d.get("content", "")
        author = d.get("author", {})
        username = author.get("username", "unknown")
        print(f"[QQBot] Guild msg from {username}: {content}")

def send_msg(channel_id, text, msg_id=None):
    data = json.dumps({"content": text})
    if msg_id:
        data = json.dumps({"content": text, "msg_id": msg_id})
    
    url = f"https://api.sgroup.qq.com/channels/{channel_id}/messages"
    req = urllib.request.Request(url, data=data.encode(), method="POST")
    req.add_header("Authorization", TOKEN)
    req.add_header("Content-Type", "application/json")
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"[QQBot] Reply sent, status: {resp.status}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[QQBot] Reply error {e.code}: {body}")

def run():
    print("[QQBot] Starting...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(connect())
    
    if not success:
        print("[QQBot] Connection failed. Will retry in 10s...")
        ws = None
        threading.Timer(10, run).start()
        return
    
    # Start heartbeat
    t = threading.Thread(target=heartbeat_thread, daemon=True)
    t.start()
    
    try:
        while ws and ws.connected:
            msg = json.loads(ws.recv())
            handle_message(msg)
    except (websocket.WebSocketConnectionClosedException, ConnectionResetError, OSError) as e:
        print(f"[QQBot] Connection lost: {e}")
    except Exception as e:
        print(f"[QQBot] Error: {e}")
    finally:
        if ws:
            try: ws.close()
            except: pass
        print("[QQBot] Reconnecting in 5s...")
        threading.Timer(5, run).start()

if __name__ == "__main__":
    try:
        import websocket
    except ImportError:
        print("[QQBot] Installing websocket-client...")
        os.system(f"{sys.executable} -m pip install websocket-client -q")
        import websocket
    
    run()
    
    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if ws:
            ws.close()
        print("[QQBot] Stopped")
