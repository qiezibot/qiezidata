#!/usr/bin/env python3
"""自动剪辑：治愈风 - 慢镜头+柔光调色+BGM"""
import subprocess, os

FFMPEG = r"C:\temp\ffmpeg.exe"
INPUT = r"C:\Users\lfy20\.openclaw\media\qqbot\downloads\1904006743\CC26706F41E5B48C18ADF3C2A2AF86A0\403c15ae-ef05-4640-8761-d6d7d09126fc.mp4"
OUTPUT = r"C:\temp\pics\output_healing.mp4"
BGM = r"C:\temp\pics\bgm.mp3"

# 下载一个免费治愈BGM
import requests
bgm_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
if not os.path.exists(BGM):
    r = requests.get(bgm_url, timeout=30)
    with open(BGM, "wb") as f:
        f.write(r.content)
    print("BGM下载完成")

# 剪辑：0.7倍慢速 + 柔光滤镜 + BGM
cmd = [
    FFMPEG, "-y",
    "-i", INPUT,
    "-stream_loop", "-1", "-i", BGM,  # BGM循环
    "-filter_complex",
    "[0:v]setpts=1.43*PTS,"
    "eq=brightness=0.08:contrast=0.9:saturation=1.3,"
    "hue=s=0,"
    "format=yuv420p[slowv];"
    "[1:a]volume=0.3[bgm];"
    "[0:a]volume=1.5[orig];"
    "[orig][bgm]amix=inputs=2:duration=first[aout]",
    "-map", "[slowv]",
    "-map", "[aout]",
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "22",
    "-c:a", "aac",
    "-b:a", "128k",
    "-movflags", "+faststart",
    "-shortest",
    OUTPUT
]

print("正在剪辑治愈风视频...")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
print("完成!" if result.returncode == 0 else "失败: " + result.stderr[-300:])

size = os.path.getsize(OUTPUT) / 1024 / 1024
print(f"输出: {OUTPUT} ({size:.1f}MB)")
