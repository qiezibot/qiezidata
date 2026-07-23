#!/usr/bin/env python3
"""自动剪辑：修复版 - 保持原色，只做微调"""
import subprocess, os

FFMPEG = r"C:\temp\ffmpeg.exe"
INPUT = r"C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\403c15ae-ef05-4640-8761-d6d7d09126fc.mp4"

# 版本1：故事感（正常速度+加亮一点点+去噪）
OUT1 = r"C:\temp\pics\v1_story_fix.mp4"
cmd1 = [
    FFMPEG, "-y", "-i", INPUT,
    "-vf", "eq=brightness=0.03:contrast=1.05,unsharp=3:3:0.5",
    "-af", "volume=2.0",
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
    OUT1
]

# 版本2：治愈风（慢速+去黑白+暖色调+BGM）
BGM = r"C:\temp\pics\bgm.mp3"
OUT2 = r"C:\temp\pics\v2_healing_fix.mp4"
if not os.path.exists(BGM):
    import requests
    r = requests.get("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", timeout=30)
    with open(BGM, "wb") as f: f.write(r.content)

cmd2 = [
    FFMPEG, "-y",
    "-i", INPUT,
    "-stream_loop", "-1", "-i", BGM,
    "-filter_complex",
    "[0:v]setpts=1.43*PTS,"
    "eq=brightness=0.05:contrast=1.0:saturation=1.1,"
    "colorbalance=rs=0.05:gs=0.02:bs=-0.02,"
    "unsharp=3:3:0.5[slowv];"
    "[1:a]volume=0.25[bgm];"
    "[0:a]volume=1.8[orig];"
    "[orig][bgm]amix=inputs=2:duration=first[aout]",
    "-map", "[slowv]",
    "-map", "[aout]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
    "-shortest",
    OUT2
]

print("剪故事感版...")
subprocess.run(cmd1, capture_output=True, timeout=120)
size1 = os.path.getsize(OUT1)/1024/1024
print(f"[OK] v1故事感: {size1:.1f}MB")

print("剪治愈风版...")
subprocess.run(cmd2, capture_output=True, timeout=180)
size2 = os.path.getsize(OUT2)/1024/1024
print(f"[OK] v2治愈风: {size2:.1f}MB")
print("两个都好了，彩色保留！")
