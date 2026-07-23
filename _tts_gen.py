
import asyncio
import edge_tts
import sys

async def main():
    text = sys.argv[1]
    out_file = sys.argv[2]
    communicate = edge_tts.Communicate(text, voice="zh-CN-XiaoxiaoNeural")
    await communicate.save(out_file)
    print(f"OK:{out_file}")

asyncio.run(main())
