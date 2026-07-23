# voice_pipeline.py - 一站式语音流水线
# TTS(edge-tts) → MP3 → WAV(24000Hz 16bit mono) → Silk (用 Node.js silk-wasm)
# 用法: python voice_pipeline.py <文字内容> <输出silk路径>

import sys, os, asyncio, subprocess

# ffmpeg 路径
FFMPEG = r'C:\Users\lfy20\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'
# silk 编码脚本
ENCODE_SILK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'encode_silk.cjs')

out_path = sys.argv[2] if len(sys.argv) > 2 else None
if not out_path:
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice.silk')

text = sys.argv[1] if len(sys.argv) > 1 else '你好'

tmp_dir = os.environ.get('TEMP', 'C:\\temp\\tts')
os.makedirs(tmp_dir, exist_ok=True)
tmp_mp3 = os.path.join(tmp_dir, '_zz_tmp.mp3')
tmp_wav = os.path.join(tmp_dir, '_zz_tmp.wav')

async def main():
    # 1. TTS → MP3 (edge-tts)
    import edge_tts
    tts = edge_tts.Communicate(text, 'zh-CN-XiaoxiaoNeural')
    await tts.save(tmp_mp3)

    # 2. MP3 → WAV 24000Hz 16bit mono (ffmpeg)
    subprocess.run([
        FFMPEG, '-y', '-i', tmp_mp3,
        '-ar', '24000', '-ac', '1', '-sample_fmt', 's16',
        tmp_wav
    ], check=True, capture_output=True)

    # 3. WAV → Silk (Node.js silk-wasm)
    subprocess.run([
        'node', ENCODE_SILK, tmp_wav, out_path
    ], check=True, capture_output=True)
    
    # 清理临时文件
    for f in [tmp_mp3, tmp_wav]:
        try:
            os.remove(f)
        except:
            pass
    
    size = os.path.getsize(out_path)
    print(f'OK:{out_path}:{size}')

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
        loop.close()
    else:
        asyncio.run(main())
