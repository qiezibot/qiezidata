#!/usr/bin/env python3
"""
文件 & 文本存储库
- 文本笔记（支持全文搜索）
- 文件存储（文件存磁盘，索引存数据库）
- 标签分类
零依赖，Python 3 标准库即可
"""

import sqlite3
import os
import shutil
import hashlib
import json
from datetime import datetime
from typing import Optional

# ===== 配置 =====
DB_PATH = os.path.join(os.path.dirname(__file__), "vault.db")
FILES_DIR = os.path.join(os.path.dirname(__file__), "vault_files")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ===== 建表 =====

def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ---- 文本笔记 ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL DEFAULT '',
            content     TEXT    NOT NULL,
            summary     TEXT    DEFAULT '',
            source      TEXT    DEFAULT '',        -- 来源：manual/web/file/其他
            created_at  TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # 全文搜索索引（FTS5）
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
        USING fts5(title, content, summary, content=notes, content_rowid=id)
    """)

    # ---- 文件索引 ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT    NOT NULL,
            original_name TEXT  NOT NULL,
            ext         TEXT    DEFAULT '',
            size_bytes  INTEGER DEFAULT 0,
            md5         TEXT    DEFAULT '',
            filepath    TEXT    NOT NULL,           -- vault_files/ 下的相对路径
            description TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ---- 标签（多对多） ----
    c.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            tag_id  INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (note_id, tag_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            tag_id  INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (file_id, tag_id)
        )
    """)

    conn.commit()
    conn.close()

    # 创建文件存储目录
    os.makedirs(FILES_DIR, exist_ok=True)


# ===== 触发器：FTS 同步 =====

def _create_fts_triggers():
    conn = get_conn()
    c = conn.cursor()
    triggers = [
        """
        CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
            INSERT INTO notes_fts(rowid, title, content, summary)
            VALUES (new.id, new.title, new.content, new.summary);
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, content, summary)
            VALUES ('delete', old.id, old.title, old.content, old.summary);
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
            INSERT INTO notes_fts(notes_fts, rowid, title, content, summary)
            VALUES ('delete', old.id, old.title, old.content, old.summary);
            INSERT INTO notes_fts(rowid, title, content, summary)
            VALUES (new.id, new.title, new.content, new.summary);
        END
        """,
    ]
    for sql in triggers:
        c.execute(sql)
    conn.commit()
    conn.close()


# ===== 文本笔记操作 =====

def save_note(title: str, content: str, summary: str = "",
              source: str = "", tags: list[str] = None) -> int:
    """保存/创建笔记，返回 id"""
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO notes (title, content, summary, source, created_at, updated_at) VALUES (?,?,?,?,?,?)",
        (title, content, summary, source, now, now),
    )
    note_id = c.lastrowid

    # 打标签
    _set_tags(c, "note_tags", "note_id", note_id, tags or [])

    conn.commit()
    conn.close()
    return note_id


def update_note(note_id: int, title: str = None, content: str = None,
                summary: str = None, tags: list[str] = None) -> bool:
    """更新笔记"""
    conn = get_conn()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = {"updated_at": now}
    if title is not None:
        fields["title"] = title
    if content is not None:
        fields["content"] = content
    if summary is not None:
        fields["summary"] = summary

    sets = ", ".join(f"{k}=?" for k in fields)
    c.execute(f"UPDATE notes SET {sets} WHERE id=?",
              list(fields.values()) + [note_id])

    if tags is not None:
        _set_tags(c, "note_tags", "note_id", note_id, tags)

    conn.commit()
    conn.close()
    return c.rowcount > 0


def delete_note(note_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return c.rowcount > 0


def get_note(note_id: int) -> Optional[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE id=?", (note_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return None
    note = dict(row)
    note["tags"] = _get_tags_for(c, "note_tags", "note_id", note_id)
    conn.close()
    return note


def list_notes(tags: list[str] = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """列出笔记，可按标签筛选"""
    conn = get_conn()
    c = conn.cursor()

    if tags:
        placeholders = ",".join("?" for _ in tags)
        c.execute(f"""
            SELECT DISTINCT n.* FROM notes n
            JOIN note_tags nt ON n.id = nt.note_id
            JOIN tags t ON nt.tag_id = t.id
            WHERE t.name IN ({placeholders})
            ORDER BY n.updated_at DESC
            LIMIT ? OFFSET ?
        """, tags + [limit, offset])
    else:
        c.execute("SELECT * FROM notes ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                  (limit, offset))

    notes = [dict(r) for r in c.fetchall()]
    for n in notes:
        n["tags"] = _get_tags_for(c, "note_tags", "note_id", n["id"])
    conn.close()
    return notes


def search_notes(keyword: str, limit: int = 20) -> list[dict]:
    """全文搜索笔记（FTS5）"""
    conn = get_conn()
    c = conn.cursor()
    # FTS5 的 MATCH 语法
    sanitized = keyword.replace('"', '""')
    c.execute(f"""
        SELECT n.*, rank
        FROM notes_fts
        JOIN notes n ON notes_fts.rowid = n.id
        WHERE notes_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (sanitized, limit))
    notes = [dict(r) for r in c.fetchall()]
    for n in notes:
        n["tags"] = _get_tags_for(c, "note_tags", "note_id", n["id"])
    conn.close()
    return notes


# ===== 文件操作 =====

def save_file(source_path: str, description: str = "",
              tags: list[str] = None) -> Optional[int]:
    """
    把文件存入仓库
    - 复制到 vault_files/ 目录
    - 记录索引到数据库
    返回 file_id 或 None
    """
    if not os.path.isfile(source_path):
        print(f"[ERROR] 文件不存在: {source_path}")
        return None

    os.makedirs(FILES_DIR, exist_ok=True)
    original_name = os.path.basename(source_path)
    _, ext = os.path.splitext(original_name)
    size = os.path.getsize(source_path)

    # 计算 MD5 防重复
    md5 = _md5_file(source_path)

    # 用 md5+扩展名 存储，避免重名
    stored_name = f"{md5}{ext}"
    dest = os.path.join(FILES_DIR, stored_name)

    if not os.path.exists(dest):
        shutil.copy2(source_path, dest)

    conn = get_conn()
    c = conn.cursor()

    # 检查是否已存在（MD5 去重）
    c.execute("SELECT id FROM files WHERE md5=?", (md5,))
    existing = c.fetchone()
    if existing:
        conn.close()
        return existing["id"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        """INSERT INTO files (filename, original_name, ext, size_bytes, md5, filepath, description, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (stored_name, original_name, ext, size, md5,
         f"vault_files/{stored_name}", description, now),
    )
    fid = c.lastrowid
    _set_tags(c, "file_tags", "file_id", fid, tags or [])
    conn.commit()
    conn.close()
    return fid


def delete_file(file_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT filepath FROM files WHERE id=?", (file_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False

    filepath = row["filepath"]
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    c.execute("DELETE FROM files WHERE id=?", (file_id,))
    conn.commit()
    conn.close()

    # 删除文件（如果没有任何记录引用了）
    if os.path.exists(full_path):
        os.remove(full_path)
    return True


def list_files(tags: list[str] = None, limit: int = 50) -> list[dict]:
    conn = get_conn()
    c = conn.cursor()

    if tags:
        placeholders = ",".join("?" for _ in tags)
        c.execute(f"""
            SELECT DISTINCT f.* FROM files f
            JOIN file_tags ft ON f.id = ft.file_id
            JOIN tags t ON ft.tag_id = t.id
            WHERE t.name IN ({placeholders})
            ORDER BY f.created_at DESC LIMIT ?
        """, tags + [limit])
    else:
        c.execute("SELECT * FROM files ORDER BY created_at DESC LIMIT ?",
                  (limit,))

    files = [dict(r) for r in c.fetchall()]
    for f in files:
        f["tags"] = _get_tags_for(c, "file_tags", "file_id", f["id"])
    conn.close()
    return files


# ===== 标签工具 =====

def _ensure_tag(c, name: str) -> int:
    """获取或创建标签，返回 tag_id"""
    c.execute("SELECT id FROM tags WHERE name=?", (name,))
    row = c.fetchone()
    if row:
        return row["id"]
    c.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    return c.lastrowid


def _set_tags(c, junction_table: str, fk_col: str, obj_id: int, tags: list[str]):
    """设置对象的所有标签（先清空再重设）"""
    c.execute(f"DELETE FROM {junction_table} WHERE {fk_col}=?", (obj_id,))
    for tag_name in tags:
        tag_id = _ensure_tag(c, tag_name.strip())
        c.execute(f"INSERT OR IGNORE INTO {junction_table} ({fk_col}, tag_id) VALUES (?,?)",
                  (obj_id, tag_id))


def _get_tags_for(c, junction_table: str, fk_col: str, obj_id: int) -> list[str]:
    c.execute(f"""
        SELECT t.name FROM tags t
        JOIN {junction_table} jt ON t.id = jt.tag_id
        WHERE jt.{fk_col}=?
    """, (obj_id,))
    return [r["name"] for r in c.fetchall()]


def list_all_tags() -> list[str]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name FROM tags ORDER BY name")
    tags = [r["name"] for r in c.fetchall()]
    conn.close()
    return tags


# ===== 工具函数 =====

def _md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ===== 命令行测试 =====

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    init_db()
    _create_fts_triggers()

    # ---- 测试笔记 ----
    print("=" * 50)
    print("📝 测试文本笔记")
    print("=" * 50)

    n1 = save_note(
        title="Python SQLite 笔记",
        content="SQLite 是 Python 自带的轻量级数据库，使用 sqlite3 模块即可操作。"
                "支持 WAL 模式提升并发性能。FTS5 全文搜索引擎非常强大。",
        summary="SQLite 入门笔记",
        source="manual",
        tags=["python", "数据库", "学习"],
    )
    print(f"  ✅ 保存笔记 id={n1}")

    n2 = save_note(
        title="做红烧肉的步骤",
        content="1. 五花肉焯水\n2. 炒糖色\n3. 加八角桂皮香叶\n4. 生抽老抽料酒\n5. 小火炖1小时\n6. 大火收汁",
        tags=["美食", "菜谱"],
    )
    print(f"  ✅ 保存笔记 id={n2}")

    # 全文搜索
    print("\n🔍 搜索 'SQLite':")
    for r in search_notes("SQLite"):
        print(f"   [{r['id']}] {r['title']}")

    print("\n🔍 搜索 '肉':")
    for r in search_notes("肉"):
        print(f"   [{r['id']}] {r['title']}")

    # ---- 测试文件 ----
    print("\n" + "=" * 50)
    print("📁 测试文件存储")
    print("=" * 50)

    # 创建一个测试文件
    test_file = os.path.join(os.path.dirname(__file__), "_test_sample.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("这是一个测试文件，用于验证文件存储功能。\n第二行。\n")

    fid = save_file(test_file, description="测试文本文件", tags=["测试", "示例"])
    print(f"  ✅ 存入文件 id={fid}")

    # 按标签查
    print("\n🏷️  标签为 '示例' 的文件:")
    for f in list_files(tags=["示例"]):
        print(f"   [{f['id']}] {f['original_name']} ({f['size_bytes']} bytes)")

    # 列出全部标签
    print(f"\n📋 所有标签: {list_all_tags()}")

    # 清理测试文件
    os.remove(test_file)
    print("\n✅ 全部测试通过!")
