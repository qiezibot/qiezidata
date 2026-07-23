#!/usr/bin/env python3
"""
TG Cloud 数据库后台
自带网页管理界面（一个文件全搞定）
启动后浏览器打开 http://localhost:5000
"""

import os
import sys
import json
import hashlib
import mimetypes
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ===== 配置 =====
BOT_TOKEN = "8733853863:AAFpd8YRNlQDVFVBr1U1zpwm2Cjv-q7LnUw"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
PORT = 5000
INDEX_FILE = os.path.join(os.path.dirname(__file__), "tg_cloud_index.json")


# ===== 数据层 =====

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "kv" not in data: data["kv"] = {}
            return data
    return {"files": [], "notes": [], "kv": {}}


def save_index(index):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _my_id():
    index = load_index()
    return index.get("user_id")


def import_requests():
    """延迟导入 requests（仅在需要 TG 同步时）"""
    import requests as req
    return req


def tg_send_message(chat_id, text):
    try:
        req = import_requests()
        req.post(f"{API_BASE}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass


# ===== HTTP 服务 =====

class DBHandler(BaseHTTPRequestHandler):

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _error(self, msg, status=400):
        self._json({"ok": False, "error": msg}, status)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0: return {}
        raw = self.rfile.read(length)
        try: return json.loads(raw)
        except: return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)

        # ===== 网页管理界面 =====
        if path == "" or path == "/":
            self._html(ADMIN_HTML)
            return

        # ===== API =====
        if path == "/api/status":
            index = load_index()
            self._json({"ok": True, "data": {
                "status": "running",
                "user_id": _my_id(),
                "kv_count": len(index.get("kv", {})),
                "note_count": len(index.get("notes", [])),
                "file_count": len(index.get("files", [])),
            }})

        elif path == "/api/kv":
            index = load_index()
            items = [{"key": k, "value": v} for k, v in index.get("kv", {}).items()]
            # 搜索
            search = query.get("search", [None])[0]
            if search:
                items = [i for i in items if search.lower() in i["key"].lower()]
            self._json({"ok": True, "data": items})

        elif path.startswith("/api/kv/"):
            key = path[8:]
            index = load_index()
            val = index.get("kv", {}).get(key)
            if val is None:
                self._error("not found", 404)
            else:
                self._json({"ok": True, "data": {"key": key, "value": val}})

        elif path == "/api/notes":
            index = load_index()
            notes = list(reversed(index.get("notes", [])))
            search = query.get("search", [None])[0]
            if search:
                s = search.lower()
                notes = [n for n in notes if
                         s in n.get("title", "").lower() or
                         s in n.get("content", "").lower()]
            tag = query.get("tag", [None])[0]
            if tag:
                notes = [n for n in notes if tag in n.get("tags", [])]
            self._json({"ok": True, "data": notes})

        elif path == "/api/files":
            index = load_index()
            self._json({"ok": True, "data": list(reversed(index.get("files", [])))})

        elif path == "/api/tags":
            index = load_index()
            tags = set()
            for n in index.get("notes", []):
                for t in n.get("tags", []):
                    tags.add(t)
            self._json({"ok": True, "data": sorted(tags)})

        else:
            self._error("not found", 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()

        if path == "/api/note":
            title = body.get("title", "")
            content = body.get("content", "")
            tags = body.get("tags", [])
            if not content:
                self._error("content required")
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
            # TG 同步
            uid = _my_id()
            if uid:
                tag_str = " ".join(f"#{t}" for t in tags)
                tg_send_message(uid, f"[Note] {title}\n{content[:100]}")
            self._json({"ok": True, "data": note})

        elif path == "/api/kv":
            key = body.get("key")
            value = body.get("value")
            if not key:
                self._error("key required")
                return
            index = load_index()
            index["kv"][key] = {
                "value": value,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            save_index(index)
            uid = _my_id()
            if uid:
                val_str = str(value)[:60]
                tg_send_message(uid, f"[KV] {key} = {val_str}")
            self._json({"ok": True, "data": {"key": key, "value": value}})

        elif path == "/api/file":
            file_path = body.get("file_path", "")
            description = body.get("description", "")
            if not file_path or not os.path.isfile(file_path):
                self._error("file not found")
                return
            uid = _my_id()
            if not uid:
                self._error("not initialized")
                return
            req = import_requests()
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            with open(file_path, "rb") as f:
                result = req.post(f"{API_BASE}/sendDocument",
                                  data={"chat_id": uid, "caption": description},
                                  files={"document": f}, timeout=60).json()
            if not result.get("ok"):
                self._error("upload failed")
                return
            doc = result["result"].get("document")
            if not doc:
                self._error("not a document")
                return
            file_id = doc["file_id"]
            md5 = _md5_file(file_path)
            index = load_index()
            record = {
                "file_id": file_id, "filename": filename, "size": size,
                "md5": md5, "description": description,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            index["files"].append(record)
            save_index(index)
            self._json({"ok": True, "data": record})

        else:
            self._error("not found", 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.startswith("/api/note/"):
            try:
                note_id = int(path[10:])
            except:
                self._error("invalid id")
                return
            index = load_index()
            index["notes"] = [n for n in index["notes"] if n.get("id") != note_id]
            save_index(index)
            self._json({"ok": True})

        elif path.startswith("/api/kv/"):
            key = path[8:]
            index = load_index()
            if key in index.get("kv", {}):
                del index["kv"][key]
                save_index(index)
                self._json({"ok": True})
            else:
                self._error("not found", 404)

        else:
            self._error("not found", 404)

    def log_message(self, format, *args):
        print(f"[DB] {args[0]} {args[1]} {args[2]}")


def _md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ===== 网页管理界面（内嵌 HTML） =====
ADMIN_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TG 云数据库后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#333}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;font-weight:600}
.header .status{font-size:12px;padding:5px 12px;border-radius:12px;background:rgba(255,255,255,0.15)}
.container{max-width:1100px;margin:0 auto;padding:16px}
.tabs{display:flex;gap:2px;margin-bottom:14px;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.tab{flex:1;padding:12px;text-align:center;cursor:pointer;font-size:13px;color:#666;border:none;background:#fff;transition:.2s}
.tab:hover{background:#f5f7fa}
.tab.active{background:#1a1a2e;color:#fff}
.panel{display:none}
.panel.active{display:block}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}
.stat-card{background:#fff;border-radius:10px;padding:14px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.stat-card .num{font-size:24px;font-weight:700;color:#1a1a2e}
.stat-card .label{font-size:11px;color:#888;margin-top:2px}
.add-bar{background:#fff;border-radius:10px;padding:12px;margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.add-bar input,.add-bar textarea{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px;outline:none;flex:1;min-width:150px}
.add-bar input:focus,.add-bar textarea:focus{border-color:#16213e}
.add-bar textarea{min-height:50px;resize:vertical}
.btn{padding:8px 18px;background:#1a1a2e;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;white-space:nowrap}
.btn:hover{background:#16213e}
.btn-sm{padding:4px 10px;font-size:11px}
.btn-red{background:#e74c3c}
.btn-red:hover{background:#c0392b}
.search-bar{width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px;margin-bottom:12px;outline:none}
.search-bar:focus{border-color:#16213e}
.kv-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.kv-card{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.06);position:relative}
.kv-card .key{font-size:12px;color:#16213e;font-weight:600;margin-bottom:6px;word-break:break-all;font-family:monospace}
.kv-card .val{font-size:12px;color:#555;word-break:break-all;max-height:80px;overflow-y:auto;background:#f8f9fa;padding:6px;border-radius:4px;font-family:monospace}
.kv-card .time{font-size:11px;color:#999;margin-top:6px}
.kv-card .del{position:absolute;top:8px;right:8px;border:none;background:none;color:#ccc;cursor:pointer;font-size:14px;padding:2px 5px;border-radius:3px}
.kv-card .del:hover{background:#fee;color:#e74c3c}
.note-list{display:flex;flex-direction:column;gap:8px}
.note-card{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.note-card .t{font-size:15px;font-weight:600;color:#1a1a2e;margin-bottom:4px}
.note-card .c{font-size:13px;color:#555;line-height:1.5;white-space:pre-wrap}
.note-card .m{font-size:11px;color:#999;margin-top:6px;display:flex;justify-content:space-between;align-items:center}
.tag{display:inline-block;background:#e8edf5;color:#16213e;font-size:10px;padding:1px 8px;border-radius:10px;margin:2px}
.file-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.file-card{background:#fff;border-radius:10px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.file-card .n{font-size:13px;font-weight:600;color:#1a1a2e;word-break:break-all}
.file-card .i{font-size:11px;color:#888;margin-top:4px}
.loading{text-align:center;padding:30px;color:#999;font-size:13px}
.err{background:#fdecea;color:#c0392b;padding:10px;border-radius:8px;margin-bottom:12px;text-align:center;display:none;font-size:13px}
@media(max-width:600px){.container{padding:10px}.kv-grid,.file-grid{grid-template-columns:1fr}.header{padding:12px 14px}.header h1{font-size:17px}}
</style>
</head>
<body>

<div class="header">
    <h1>📦 TG 云数据库</h1>
    <div class="status" id="status">检测中...</div>
</div>

<div class="container">
    <div class="stats">
        <div class="stat-card"><div class="num" id="s-kv">-</div><div class="label">键值对</div></div>
        <div class="stat-card"><div class="num" id="s-notes">-</div><div class="label">笔记</div></div>
        <div class="stat-card"><div class="num" id="s-files">-</div><div class="label">文件</div></div>
    </div>

    <div id="err" class="err"></div>

    <div class="tabs">
        <button class="tab active" onclick="tab('kv')">🔑 键值</button>
        <button class="tab" onclick="tab('notes')">📝 笔记</button>
        <button class="tab" onclick="tab('files')">📁 文件</button>
    </div>

    <!-- KV -->
    <div id="p-kv" class="panel active">
        <div class="add-bar">
            <input id="kvk" placeholder="键名">
            <input id="kvv" placeholder="值" style="flex:2">
            <button class="btn" onclick="kvAdd()">存入</button>
        </div>
        <input class="search-bar" placeholder="搜索键名..." oninput="kvFilter()">
        <div class="kv-grid" id="kv-list"></div>
    </div>

    <!-- Notes -->
    <div id="p-notes" class="panel">
        <div class="add-bar" style="flex-direction:column">
            <div style="display:flex;gap:8px;width:100%">
                <input id="nt" placeholder="标题" style="flex:1">
                <input id="ntags" placeholder="标签,逗号分隔" style="flex:0 0 180px">
                <button class="btn" onclick="noteAdd()">保存</button>
            </div>
            <textarea id="nc" placeholder="正文..." style="width:100%;margin-top:6px"></textarea>
        </div>
        <input class="search-bar" placeholder="搜索笔记..." oninput="noteFilter()">
        <div class="note-list" id="note-list"></div>
    </div>

    <!-- Files -->
    <div id="p-files" class="panel">
        <div class="add-bar">
            <input id="fp" placeholder="文件路径 (如 C:/a.jpg)" style="flex:3">
            <input id="fd" placeholder="描述" style="flex:1">
            <button class="btn" onclick="fileUpload()">上传</button>
        </div>
        <div class="file-grid" id="file-list"></div>
    </div>
</div>

<script>
const API='';

async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json'}};if(b)o.body=JSON.stringify(b);const r=await fetch(API+p,o);if(!r.ok)throw await r.text();return await r.json()}
function err(s){const e=document.getElementById('err');e.textContent=s;e.style.display='block';setTimeout(()=>e.style.display='none',3000)}

async function init(){
    try{const r=await api('GET','/api/status');const d=r.data;
        document.getElementById('status').textContent='✅ 在线';document.getElementById('status').style.background='rgba(46,204,113,0.3)';
        document.getElementById('s-kv').textContent=d.kv_count;document.getElementById('s-notes').textContent=d.note_count;document.getElementById('s-files').textContent=d.file_count
    }catch(e){document.getElementById('status').textContent='❌ 离线';document.getElementById('status').style.background='rgba(231,76,60,0.3)';err('无法连接数据库服务')}
    kvLoad();noteLoad();fileLoad()
}

function tab(n){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
    document.querySelector(`.tab[onclick="tab('${n}')"]`).classList.add('active');document.getElementById('p-'+n).classList.add('active')}

// KV
async function kvLoad(){try{const r=await api('GET','/api/kv');const d=r.data||[];const el=document.getElementById('kv-list');
    el.innerHTML=d.length?d.map(i=>kvCard(i)).join(''):'<div class="loading">暂无键值数据</div>'}catch(e){document.getElementById('kv-list').innerHTML='<div class="loading">加载失败</div>'}}
function kvCard(i){const v=typeof i.value==='object'?JSON.stringify(i.value):i.value;const t=i.value?.updated_at||'';
    return `<div class="kv-card"><button class="del" onclick="kvDel('${i.key}')">×</button><div class="key">🔑 ${esc(i.key)}</div><div class="val">${esc(v)}</div>${t?'<div class="time">'+t+'</div>':''}</div>`}
async function kvAdd(){const k=document.getElementById('kvk').value.trim(),v=document.getElementById('kvv').value.trim();if(!k)return err('请输入键名');
    await api('POST','/api/kv',{key:k,value:v});document.getElementById('kvk').value='';document.getElementById('kvv').value='';kvLoad()}
async function kvDel(k){if(!confirm('删除 '+k+' ?'))return;await api('DELETE','/api/kv/'+encodeURIComponent(k));kvLoad()}
function kvFilter(){const q=document.getElementById('kv-list').parentElement.querySelector('.search-bar').value.toLowerCase();
    document.querySelectorAll('#kv-list .kv-card').forEach(c=>{c.style.display=c.textContent.toLowerCase().includes(q)?'':'none'})}

// Notes
async function noteLoad(){try{const r=await api('GET','/api/notes');const d=r.data||[];const el=document.getElementById('note-list');
    el.innerHTML=d.length?d.map(n=>noteCard(n)).join(''):'<div class="loading">暂无笔记</div>'}catch(e){document.getElementById('note-list').innerHTML='<div class="loading">加载失败</div>'}}
function noteCard(n){const tg=(n.tags||[]).map(t=>`<span class="tag">#${t}</span>`).join('');
    return `<div class="note-card"><div class="t">${esc(n.title||'无标题')}</div><div class="c">${esc(n.content)}</div> ${tg?'<div style="margin-top:4px">'+tg+'</div>':''}<div class="m"><span>${n.saved_at||''}</span><button class="btn btn-sm btn-red" onclick="noteDel(${n.id})">删除</button></div></div>`}
async function noteAdd(){const t=document.getElementById('nt').value.trim(),c=document.getElementById('nc').value.trim(),ts=document.getElementById('ntags').value.trim();
    if(!c)return err('请输入内容');const tags=ts?ts.split(',').map(x=>x.trim()).filter(Boolean):[];
    await api('POST','/api/note',{title:t,content:c,tags});document.getElementById('nt').value='';document.getElementById('nc').value='';document.getElementById('ntags').value='';noteLoad()}
async function noteDel(id){if(!confirm('删除此笔记？'))return;await api('DELETE','/api/note/'+id);noteLoad()}
function noteFilter(){const q=document.getElementById('note-list').parentElement.querySelector('.search-bar').value.toLowerCase();
    document.querySelectorAll('#note-list .note-card').forEach(c=>c.style.display=c.textContent.toLowerCase().includes(q)?'':'none')}

// Files
async function fileLoad(){try{const r=await api('GET','/api/files');const d=r.data||[];const el=document.getElementById('file-list');
    el.innerHTML=d.length?d.map(f=>fileCard(f)).join(''):'<div class="loading">暂无文件</div>'}catch(e){document.getElementById('file-list').innerHTML='<div class="loading">加载失败</div>'}}
function fileCard(f){const sz=f.size?fs(f.size):'';return `<div class="file-card"><div class="n">📄 ${esc(f.filename)}</div><div class="i">${sz} · ${f.uploaded_at||''}</div>${f.description?'<div class="i">'+esc(f.description)+'</div>':''}</div>`}
async function fileUpload(){const p=document.getElementById('fp').value.trim(),d=document.getElementById('fd').value.trim();if(!p)return err('请输入文件路径');
    await api('POST','/api/file',{file_path:p,description:d});document.getElementById('fp').value='';document.getElementById('fd').value='';fileLoad()}
function fs(b){if(b<1024)return b+'B';if(b<1048576)return(b/1024).toFixed(1)+'KB';return(b/1048576).toFixed(1)+'MB'}
function esc(s){const e=document.createElement('div');e.textContent=s;return e.innerHTML}

init()
</script>
</body>
</html>"""


# ===== 启动 =====

def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    index = load_index()
    if "user_id" not in index:
        print("❌ 未初始化！请先运行: python tg_cloud.py init")
        sys.exit(1)

    server = HTTPServer(("0.0.0.0", PORT), DBHandler)
    print(f"\n{'='*50}")
    print(f"📦 TG 云数据库后台已启动")
    print(f"{'='*50}")
    print(f"   本地: http://localhost:{PORT}")
    print(f"   本机: http://{_get_ip()}:{PORT}")
    print(f"{'='*50}")
    print(f"   键值存储: POST /api/kv   GET /api/kv/<key>")
    print(f"   笔记:     POST /api/note GET /api/notes")
    print(f"   文件:     POST /api/file GET /api/files")
    print(f"   状态:     GET /api/status")
    print(f"{'='*50}")
    print(f"   按 Ctrl+C 停止\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")


def _get_ip():
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
    main()
