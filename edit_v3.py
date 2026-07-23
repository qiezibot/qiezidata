#!/usr/bin/env python3
"""治愈风修复版 - 保持原速，只做调色+BGM"""
import subprocess, os

FFMPEG = r"C:\temp\ffmpeg.exe"
INPUT = r"C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\403c15ae-ef05-4640-8761-d6d7d09126fc.mp4"
OUT = r"C:\temp\pics\v3_healing_final.mp4"
BGM = r"C:\temp\pics\bgm.mp3"

if not os.path.exists(BGM):
    import requests
    r = requests.get("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", timeout=30)
    with open(BGM, "wb") as f: f.write(r.content)

# 不改变视频速度！原速播放，只叠加BGM
cmd = [
    FFMPEG, "-y",
    "-i", INPUT,
    "-stream_loop", "-1", "-i", BGM,
    "-filter_complex",
    "[0:v]eq=brightness=0.05:contrast=1.02:saturation=1.1,"
    "colorbalance=rs=0.03:gs=0.01,"
    "unsharp=3:3:0.3[v];"
    "[1:a]volume=0.2[bgm];"
    "[0:a]volume=1.8[orig];"
    "[orig][bgm]amix=inputs=2:duration=first:weights=1 0.4[a]",
    "-map", "[v]",
    "-map", "[a]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart",
    "-shortest",
    OUT
]

print("剪治愈风（原速+BGM）...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
if result.returncode == 0:
    print(f"OK! {os.path.getsize(OUT)/1024/1024:.1f}MB")
else:
    print("失败:", result.stderr[-300:])
