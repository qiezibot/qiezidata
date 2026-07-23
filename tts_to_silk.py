"""
tts_to_silk.py - 文字转QQ语音(.silk)
用法: python tts_to_silk.py "要说的文字" 输出文件路径.silk

依赖: pip install edge-tts pysilk
需要 ffmpeg 在 PATH 或指定路径
"""

import asyncio
import edge_tts
import sys
import os
import subprocess
import tempfile
import shutil
import json

# ffmpeg 路径
FFMPEG = r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"

# 保存修复状态文件，重启后不丢失
FIX_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_status.json')
def save_fix_status():
    try:
        import pysilk
        ver = getattr(pysilk, '__version__', 'unknown')
        status = {
            'pysilk_version': ver,
            'last_fix': '2026-05-16',
            'tts_script': os.path.abspath(__file__),
            'status': 'ok'
        }
        with open(FIX_STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
    except:
        pass

async def text_to_silk(text: str, out_file: str) -> str:
    """将文字转为QQ语音silk文件"""
    out_file = os.path.abspath(out_file)
    out_dir = os.path.dirname(out_file)
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. edge-tts 生成 MP3
    tmp_mp3 = out_file.replace('.silk', '_tmp.mp3')
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save(tmp_mp3)
    
    # 2. ffmpeg 转 WAV (24000Hz, 16bit, mono)
    tmp_wav = out_file.replace('.silk', '_tmp.wav')
    subprocess.run(
        [FFMPEG, '-y', '-i', tmp_mp3, '-ar', '24000', '-ac', '1', 
         '-sample_fmt', 's16', tmp_wav],
        check=True, capture_output=True
    )
    
    # 3. pysilk 转 .silk (新版API: 传文件对象 + bit_rate)
    import pysilk
    with open(tmp_wav, 'rb') as fin:
        with open(out_file, 'wb') as fout:
            pysilk.encode(fin, fout, 24000, 24000)
    
    # 清理临时文件
    for f in [tmp_mp3, tmp_wav]:
        try:
            os.remove(f)
        except:
            pass
    
    return out_file

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python tts_to_silk.py '文字' 输出文件.silk")
        sys.exit(1)
    
    text = sys.argv[1]
    out_file = sys.argv[2]
    
    result = asyncio.run(text_to_silk(text, out_file))
    print(f"OK:{result}")
