#!/usr/bin/env python3
"""
示例：在脚本中调用 tg_cloud 存数据
"""

import sys
import os

# 确保能 import tg_cloud
sys.path.insert(0, os.path.dirname(__file__))

# ===== 方式1：直接调用命令行 =====
def save_by_subprocess():
    """通过 subprocess 调用（最简单）"""
    import subprocess
    subprocess.run([
        sys.executable, "tg_cloud.py", "note",
        "--title", "来自脚本的笔记",
        "--content", "这是脚本自动存的",
        "--tags", "脚本,自动"
    ], cwd=os.path.dirname(__file__))


# ===== 方式2：直接调函数（推荐）=====
# 先在 tg_cloud.py 里把这些函数暴露出来就可以
from tg_cloud import (
    save_note,
    upload_file,
    list_files,
    list_notes,
    search_notes,
    download_file_by_name,
    init_db,  # 如果 tg_cloud 有 init_db
)


# 示例：存笔记
def example_save_note():
    save_note(
        title="每日总结",
        content="今天搞定了 TG 云存储脚本",
        tags=["日记", "项目"],
    )


# 示例：存文件
def example_upload():
    # 自动上传某个文件
    upload_file("C:/temp/report.txt", description="自动生成的报告")


# 示例：查看所有
def example_list_all():
    print("=== 文件列表 ===")
    list_files()
    print("\n=== 笔记列表 ===")
    list_notes()


if __name__ == "__main__":
    # 一键存条笔记
    example_save_note()

    # 也可以传参进来
    if len(sys.argv) >= 3:
        save_note(title=sys.argv[1], content=sys.argv[2])
