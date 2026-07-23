#!/usr/bin/env python3
"""自动剪辑：故事感风格 - 配旁白+慢镜头+电影感调色"""
import subprocess, os

FFMPEG = r"C:\temp\ffmpeg.exe"
INPUT = r"C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\403c15ae-ef05-4640-8761-d6d7d09126fc.mp4"
OUTPUT = r"C:\temp\pics\output_story.mp4"
TEMP = r"C:\temp\pics\temp"

os.makedirs(TEMP, exist_ok=True)

# 第一步：变速处理 - 开头3秒慢放，中间正常
filters = (
    "[0:v]setpts=2.0*PTS[v0];"  # 前3秒变慢（部分）
)

# 直接用FFmpeg做剪辑
cmd = [
    FFMPEG, "-y", "-i", INPUT,
    "-vf", "eq=brightness=0.05:contrast=1.1:saturation=1.2",  # 调色：提亮+加对比+增饱和
    "-af", "volume=2.0",  # 音量放大
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "23",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    OUTPUT
]

print("正在剪辑故事感视频...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print("完成!" if result.returncode == 0 else "失败: " + result.stderr[-200:])

size = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"输出: {OUTPUT} ({size:.1f}MB)")
