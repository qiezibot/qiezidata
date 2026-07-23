#!/usr/bin/env python3
"""
通用 SQLite 数据存取模块
Python 3.11 + SQLite3（标准库，零依赖）
用法：先建表，然后增删改查
"""

import sqlite3
import os
from typing import Any, Optional

# ===== 配置 =====
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持按列名访问
    conn.execute("PRAGMA journal_mode=WAL")  # 性能优化
    return conn


# ===== 建表（你在这里加自己的表）=====

def init_db():
    """初始化数据库，创建所有表"""
    conn = get_conn()
    c = conn.cursor()

    # ---------- 示例表：用户 ----------
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            age         INTEGER,
            email       TEXT    UNIQUE,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ---------- 示例表：商品 ----------
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            price       REAL    NOT NULL,
            stock       INTEGER DEFAULT 0,
            category    TEXT,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # ↓↓↓ 在这里加你自己的表 ↓↓↓

    conn.commit()
    conn.close()


# ===== 增删改查 =====

def insert(table: str, data: dict) -> int:
    """
    插入一条数据
    例: insert("users", {"name": "张三", "age": 25, "email": "zs@test.com"})
    返回: 新记录的 id
    """
    conn = get_conn()
    c = conn.cursor()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    c.execute(sql, list(data.values()))
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id


def delete(table: str, where: dict = None) -> int:
    """
    删除数据
    例: delete("users", {"id": 1})         → 删除 id=1
         delete("users")                    → 删除全部（慎用！）
    返回: 影响的行数
    """
    conn = get_conn()
    c = conn.cursor()
    if where:
        clause = " AND ".join([f"{k}=?" for k in where.keys()])
        sql = f"DELETE FROM {table} WHERE {clause}"
        c.execute(sql, list(where.values()))
    else:
        sql = f"DELETE FROM {table}"
        c.execute(sql)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


def update(table: str, data: dict, where: dict) -> int:
    """
    更新数据
    例: update("users", {"age": 26}, {"id": 1})  → 把 id=1 的年龄改成 26
    返回: 影响的行数
    """
    conn = get_conn()
    c = conn.cursor()
    set_clause = ", ".join([f"{k}=?" for k in data.keys()])
    where_clause = " AND ".join([f"{k}=?" for k in where.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    c.execute(sql, list(data.values()) + list(where.values()))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected


def query(
    table: str,
    where: dict = None,
    order_by: str = None,
    limit: int = None,
) -> list[dict]:
    """
    查询数据
    例: query("users")                                    → 查全部
         query("users", {"id": 1})                         → 查 id=1
         query("users", order_by="id DESC", limit=10)      → 查最近10条
    返回: list[dict]
    """
    conn = get_conn()
    c = conn.cursor()
    sql = f"SELECT * FROM {table}"
    params = []

    if where:
        clause = " AND ".join([f"{k}=?" for k in where.keys()])
        sql += f" WHERE {clause}"
        params = list(where.values())

    if order_by:
        sql += f" ORDER BY {order_by}"

    if limit:
        sql += f" LIMIT ?"
        params.append(limit)

    c.execute(sql, params)
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def get(table: str, id_value: int) -> Optional[dict]:
    """按 id 查询单条"""
    rows = query(table, {"id": id_value})
    return rows[0] if rows else None


def count(table: str, where: dict = None) -> int:
    """统计行数"""
    conn = get_conn()
    c = conn.cursor()
    if where:
        clause = " AND ".join([f"{k}=?" for k in where.keys()])
        c.execute(f"SELECT COUNT(*) FROM {table} WHERE {clause}", list(where.values()))
    else:
        c.execute(f"SELECT COUNT(*) FROM {table}")
    result = c.fetchone()[0]
    conn.close()
    return result


# ===== 命令行测试 =====
if __name__ == "__main__":
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    init_db()

    # 插入测试数据
    uid = insert("users", {"name": "张三", "age": 25, "email": "zs@test.com"})
    print(f"[OK] 插入用户 id={uid}")

    insert("users", {"name": "李四", "age": 30, "email": "ls@test.com"})
    insert("products", {"name": "笔记本", "price": 4999, "stock": 10, "category": "数码"})

    # 查询全部
    users = query("users")
    print("\n[LIST] 所有用户:")
    for u in users:
        print(f"   {u['id']}. {u['name']} - {u['age']}岁 - {u['email']}")

    # 条件查询
    print(f"\n[SEARCH] 25岁的用户: {query('users', {'age': 25})}")

    # 更新
    update("users", {"age": 26}, {"name": "张三"})
    print(f"\n[UPDATE] 更新后: {get('users', uid)}")

    # 统计
    print(f"\n[COUNT] 用户总数: {count('users'):}")
