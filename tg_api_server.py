#!/usr/bin/env python3
"""
TG Cloud API 服务
轻量 HTTP 接口，供懒人精灵调用
启动后：python tg_api_server.py
"""

import os
import sys
import json
import hashlib
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

# ===== 配置 =====
BOT_TOKEN = "8733853863:AAFpd8YRNlQDVFVBr1U1zpwm2Cjv-q7LnUw"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

HOST = "0.0.0.0"
PORT = 8888

INDEX_FILE = os.path.join(os.path.dirname(__file__), "tg_cloud_index.json")


# ===== Telegram API =====

def _my_id():
    index = load_index()
    return index.get("user_id")


def tg_api(method, data=None, files=None):
    url = f"{API_BASE}/{method}"
    try:
        if files:
            resp = requests.post(url, data=data, files=files, timeout=30)
        else:
            resp = requests.post(url, json=data, timeout=15) if data else requests.get(url, timeout=15)
        result = resp.json()
        return result if result.get("ok") else None
    except Exception as e:
        return None


def send_message(chat_id, text):
    return tg_api("sendMessage", {"chat_id": chat_id, "text": text})


def send_document(chat_id, file_path, caption=""):
    with open(file_path, "rb") as f:
        return tg_api("sendDocument", {"chat_id": chat_id, "caption": caption}, {"document": f})


def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 兼容旧索引
            if "kv" not in data:
                data["kv"] = {}
            return data
    return {"files": [], "notes": [], "kv": {}}


def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ===== HTTP 服务 =====

class CloudAPIHandler(BaseHTTPRequestHandler):
    """HTTP API 处理器"""

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(body)

    def _send_error(self, msg, status=400):
        self._send_json({"ok": False, "error": msg}, status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except:
            return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        # GET /status - 服务状态
        if path == "/status":
            index = load_index()
            uid = _my_id()
            self._send_json({
                "ok": True,
                "data": {
                    "status": "running",
                    "user_id": uid,
                    "file_count": len(index.get("files", [])),
                    "note_count": len(index.get("notes", [])),
                    "kv_count": len(index.get("kv", {})),
                }
            })
            return

        # GET /notes - 列出笔记
        if path == "/notes":
            index = load_index()
            self._send_json({"ok": True, "data": index.get("notes", [])})
            return

        # GET /files - 列出文件
        if path == "/files":
            index = load_index()
            self._send_json({"ok": True, "data": index.get("files", [])})
            return

        # GET /kv/<key> - 读取键值
        if path.startswith("/kv/"):
            key = path[4:]
            index = load_index()
            val = index.get("kv", {}).get(key)
            if val is None:
                self._send_error(f"key '{key}' not found", 404)
            else:
                self._send_json({"ok": True, "data": {"key": key, "value": val}})
            return

        self._send_error("not found", 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()

        # POST /note - 存笔记
        if path == "/note":
            title = body.get("title", "")
            content = body.get("content", "")
            tags = body.get("tags", [])
            if not content:
                self._send_error("content required")
                return

            index = load_index()
            note = {
                "id": len(index["notes"]) + 1,
                "title": title,
                "content": content,
                "tags": tags,
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            index["notes"].append(note)
            save_index(index)

            # 同步到 TG（静默模式）
            try:
                uid = _my_id()
                if uid and content.strip():
                    msg = f"[Note] {title}\n{content[:100]}"
                    threading.Thread(target=send_message, args=(uid, msg), daemon=True).start()
            except:
                pass

            self._send_json({"ok": True, "data": note})
            return

        # POST /kv - 存键值
        if path == "/kv":
            key = body.get("key")
            value = body.get("value")
            if not key:
                self._send_error("key required")
                return

            index = load_index()
            index["kv"][key] = {
                "value": value,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_index(index)

            # TG 同步（静默）
            try:
                uid = _my_id()
                if uid:
                    val_str = json.dumps(value, ensure_ascii=False)[:80]
                    threading.Thread(target=send_message, args=(uid, f"[KV] {key} = {val_str}"), daemon=True).start()
            except:
                pass

            self._send_json({"ok": True, "data": {"key": key, "value": value}})
            return

        # POST /file - 上传文件
        if path == "/file":
            file_path = body.get("file_path", "")
            description = body.get("description", "")
            tags = body.get("tags", [])

            if not file_path or not os.path.isfile(file_path):
                self._send_error("file not found")
                return

            uid = _my_id()
            if not uid:
                self._send_error("not initialized")
                return

            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)

            result = send_document(uid, file_path, description)
            if not result:
                self._send_error("upload failed")
                return

            doc = result.get("document")
            if not doc:
                self._send_error("not a document")
                return

            file_id = doc["file_id"]
            md5 = _md5_file(file_path)

            index = load_index()
            record = {
                "file_id": file_id,
                "filename": filename,
                "size": size,
                "md5": md5,
                "description": description,
                "tags": tags,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            index["files"].append(record)
            save_index(index)

            self._send_json({"ok": True, "data": record})
            return

        self._send_error("not found", 404)

    def do_DELETE(self):
        path = self.path.split("?")[0]

        # DELETE /note/<id>
        if path.startswith("/note/"):
            try:
                note_id = int(path[6:])
            except:
                self._send_error("invalid id")
                return
            index = load_index()
            index["notes"] = [n for n in index["notes"] if n.get("id") != note_id]
            save_index(index)
            self._send_json({"ok": True})
            return

        # DELETE /kv/<key>
        if path.startswith("/kv/"):
            key = path[4:]
            index = load_index()
            if key in index.get("kv", {}):
                del index["kv"][key]
                save_index(index)
                self._send_json({"ok": True})
            else:
                self._send_error("key not found", 404)
            return

        self._send_error("not found", 404)

    def log_message(self, format, *args):
        print(f"[API] {args[0]} {args[1]} -> {args[2]}")


def _md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ===== 启动服务 =====

def main():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    # 检查初始化
    index = load_index()
    if "user_id" not in index:
        print("❌ 未初始化！请先运行: python tg_cloud.py init")
        print("   然后启动本服务")
        sys.exit(1)

    server = HTTPServer((HOST, PORT), CloudAPIHandler)
    print(f"✅ TG Cloud API 服务已启动")
    print(f"   地址: http://localhost:{PORT}")
    print(f"   本机IP: http://{_get_local_ip()}:{PORT}")
    print(f"   接口:")
    print(f"     GET  /status     - 服务状态")
    print(f"     GET  /notes      - 笔记列表")
    print(f"     GET  /files      - 文件列表")
    print(f"     GET  /kv/<key>   - 读取键值")
    print(f"     POST /note       - 存笔记")
    print(f"     POST /kv         - 存键值")
    print(f"     POST /file       - 上传文件")
    print(f"     DELETE /note/<id> - 删笔记")
    print(f"     DELETE /kv/<key>  - 删键值")
    print(f"   按 Ctrl+C 停止")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


def _get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    import io
    main()
