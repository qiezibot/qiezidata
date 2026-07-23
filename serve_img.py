import http.server, socketserver, threading, os

PORT = 18888
DIR = r"C:\Users\lfy20\Downloads"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def log_message(self, *a):
        pass

httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
t = threading.Thread(target=httpd.serve_forever, daemon=True)
t.start()
print(f"HTTP server on http://127.0.0.1:{PORT}")
import time
time.sleep(3600)
