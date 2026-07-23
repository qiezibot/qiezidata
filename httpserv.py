import http.server, socketserver, threading, os
from http.server import SimpleHTTPRequestHandler

os.chdir("C:/Users/lfy20/Downloads")

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

d = socketserver.TCPServer(("127.0.0.1", 18888), Handler)
t = threading.Thread(target=d.serve_forever, daemon=True)
t.start()
print("HTTP server on 18888")
threading.Event().wait()
