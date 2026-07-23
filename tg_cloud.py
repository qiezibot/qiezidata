#!/usr/bin/env python3
"""
Telegram 云存储 —— 白嫖方案
用 Telegram Bot 免费存文件 & 文本
"""

import os
import sys
import json
import hashlib
import mimetypes
from datetime import datetime

import requests

# ===== 配置 =====
BOT_TOKEN = "8733853863:AAFpd8YRNlQDVFVBr1U1zpwm2Cjv-q7LnUw"
API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 本地索引文件（记录存了什么）
INDEX_FILE = os.path.join(os.path.dirname(__file__), "tg_cloud_index.json")
# 下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "tg_downloads")

# 你的 TG 用户 ID（第一次运行时会自动获取）
YOUR_USER_ID = None


# ===== Telegram API 调用 =====

def tg_api(method: str, data: dict = None, files: dict = None) -> dict:
    """调用 Telegram Bot API"""
    url = f"{API_BASE}/{method}"
    if files:
        resp = requests.post(url, data=data, files=files, timeout=60)
    else:
        resp = requests.post(url, json=data, timeout=30) if data else requests.get(url, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        print(f"[ERROR] Telegram API 错误: {result}")
        return None
    return result["result"]


def get_me() -> dict:
    return tg_api("getMe")


def get_updates(offset: int = None) -> list:
    data = {"timeout": 5}
    if offset:
        data["offset"] = offset
    result = tg_api("getUpdates", data)
    return result or []


def send_message(chat_id: int, text: str) -> dict:
    return tg_api("sendMessage", {"chat_id": chat_id, "text": text})


def send_document(chat_id: int, file_path: str, caption: str = "") -> dict:
    """上传文件到 Telegram"""
    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {"chat_id": chat_id, "caption": caption}
        return tg_api("sendDocument", data, files)


def get_file_info(file_id: str) -> dict:
    """获取 Telegram 上的文件信息"""
    return tg_api("getFile", {"file_id": file_id})


def download_file(file_id: str, save_path: str):
    """从 Telegram 下载文件"""
    info = get_file_info(file_id)
    if not info:
        return False
    file_path = info["file_path"]
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    resp = requests.get(url, timeout=120)
    with open(save_path, "wb") as f:
        f.write(resp.content)
    return True


# ===== 本地索引管理 =====

def load_index() -> dict:
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": [], "notes": []}


def save_index(index: dict):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ===== 核心功能 =====

def init_bot():
    """初始化：获取你的用户 ID 并保存到索引"""
    global YOUR_USER_ID
    me = get_me()
    bot_username = me["username"]
    print(f"✅ Bot 名称: @{bot_username}")

    # 取最近一条消息的 sender
    updates = get_updates()
    for upd in reversed(updates):
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat", {})
        if chat.get("type") == "private":
            YOUR_USER_ID = chat["id"]
            # 保存到索引
            index = load_index()
            index["user_id"] = YOUR_USER_ID
            index["bot_username"] = bot_username
            save_index(index)
            print(f"✅ 检测到你的用户 ID: {YOUR_USER_ID}")
            send_message(YOUR_USER_ID, "📦 TG云存储已就绪！")
            return

    print("❌ 没找到你的消息。请先给 bot 发一条消息。")
    sys.exit(1)


def _my_id() -> int:
    """从索引获取我的用户 ID"""
    index = load_index()
    return index.get("user_id")


def upload_file(file_path: str, description: str = ""):
    """上传文件到 TG"""
    if not os.path.isfile(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    uid = _my_id()
    if not uid:
        print("❌ 未初始化，先运行: python tg_cloud.py init")
        return

    index = load_index()
    filename = os.path.basename(file_path)
    size = os.path.getsize(file_path)

    print(f"📤 上传: {filename} ({_fmt_size(size)})")
    result = send_document(uid, file_path, description)

    if not result:
        print("❌ 上传失败")
        return

    doc = result.get("document")
    if not doc:
        print(f"❌ 不是文档类型: {result.get('text', '')}")
        return

    file_id = doc["file_id"]
    md5 = _md5_file(file_path)

    # 记录到索引
    record = {
        "file_id": file_id,
        "filename": filename,
        "size": size,
        "md5": md5,
        "description": description,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    index["files"].append(record)
    save_index(index)
    print(f"✅ 上传成功！file_id: {file_id}")


def download_file_by_name(filename: str):
    """按文件名从 TG 下载"""
    index = load_index()
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    matches = [f for f in index["files"] if filename in f["filename"]]
    if not matches:
        print(f"❌ 未找到匹配的文件: {filename}")
        return

    record = matches[-1]  # 取最新的
    save_path = os.path.join(DOWNLOAD_DIR, record["filename"])
    print(f"📥 下载: {record['filename']}")
    if download_file(record["file_id"], save_path):
        print(f"✅ 已保存到: {save_path}")
    else:
        print("❌ 下载失败")


def list_files():
    """列出所有已上传的文件"""
    index = load_index()
    if not index["files"]:
        print("📭 还没有存任何文件")
        return

    print(f"\n📁 已存储 {len(index['files'])} 个文件:")
    print("-" * 60)
    for i, f in enumerate(index["files"], 1):
        desc = f" - {f['description']}" if f.get("description") else ""
        print(f"  {i}. {f['filename']} ({_fmt_size(f['size'])}){desc}")
        print(f"     上传于: {f['uploaded_at']}")


# ===== 文本笔记 =====

def save_note(title: str, content: str, tags: list = None):
    """保存文本笔记到索引"""
    index = load_index()
    note = {
        "id": len(index["notes"]) + 1,
        "title": title,
        "content": content,
        "tags": tags or [],
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    index["notes"].append(note)
    save_index(index)
    print(f"✅ 笔记已保存: {title}")

    # 同时也发一条到 TG 做备份
    uid = _my_id()
    if uid:
        tag_str = " ".join(f"#{t}" for t in (tags or []))
        msg = f"📝 {title}\n\n{content[:200]}{'...' if len(content) > 200 else ''}\n\n{tag_str}"
        send_message(uid, msg)


def list_notes():
    """列出所有笔记"""
    index = load_index()
    if not index["notes"]:
        print("📭 还没有笔记")
        return

    print(f"\n📝 共 {len(index['notes'])} 条笔记:")
    print("-" * 60)
    for n in index["notes"]:
        tags = " ".join(f"#{t}" for t in n["tags"]) if n["tags"] else ""
        print(f"  [{n['id']}] {n['title']}  {tags}")
        print(f"      {n['content'][:80]}{'...' if len(n['content']) > 80 else ''}")


# ===== 工具 =====

def _md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fmt_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


# ===== 命令行模式 =====

def main():
    import argparse

    parser = argparse.ArgumentParser(description="📦 TG 云存储")
    parser.add_argument("action", choices=["init", "upload", "download", "ls", "note", "notes"],
                        help="操作: init(初始化), upload(上传), download(下载), ls(列表), note(存笔记), notes(笔记列表)")
    parser.add_argument("--file", "-f", help="上传/下载的文件路径或文件名关键词")
    parser.add_argument("--desc", "-d", help="文件描述")
    parser.add_argument("--title", "-t", help="笔记标题")
    parser.add_argument("--content", "-c", help="笔记内容")
    parser.add_argument("--tags", help="标签，逗号分隔")

    args = parser.parse_args()

    # 非 init 操作先确保已初始化
    if args.action != "init":
        index = load_index()
        if "user_id" not in index:
            print("❌ 请先运行: python tg_cloud.py init")
            return

    if args.action == "init":
        init_bot()
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    elif args.action == "upload":
        if not args.file:
            print("❌ 请指定文件路径: --file / -f")
            return
        upload_file(args.file, args.desc or "")

    elif args.action == "download":
        if not args.file:
            print("❌ 请指定文件名关键词: --file / -f")
            return
        download_file_by_name(args.file)

    elif args.action == "ls":
        list_files()

    elif args.action == "note":
        save_note(args.title or "", args.content or "", args.tags.split(",") if args.tags else None)

    elif args.action == "notes":
        list_notes()


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    main()
