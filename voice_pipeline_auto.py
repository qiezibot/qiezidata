# voice_pipeline_auto.py
"""
语音自动处理：声纹识别 → 根据身份回应
集成在收到语音消息时的处理流程中
"""
import os, sys, json, subprocess

VOICE_ID_SCRIPT = os.path.join(os.path.dirname(__file__), 'voice_id_v2.py')
VOICE_PIPELINE = os.path.join(os.path.dirname(__file__), 'voice_pipeline.py')
TTS_DIR = r'C:\temp\tts'

# 身份对应的称呼
GREETINGS = {
    '爹': '爹',
    '姐': '姐',
    '妈妈': '妈',
}

def recognize_speaker(audio_path, threshold=0.45):
    """声纹识别，返回 (name, score)"""
    env = os.environ.copy()
    env['PYTHONUTF8'] = '1'
    result = subprocess.run(
        ['python', VOICE_ID_SCRIPT, 'recognize', audio_path],
        capture_output=True, text=True, env=env, timeout=60
    )
    output = result.stdout + result.stderr
    
    for line in output.split('\n'):
        line = line.strip()
        if '识别结果:' in line:
            # 解析 "识别结果: 姐 (得分: 0.9984)"
            parts = line.replace('识别结果:', '').strip().split('(得分:')
            name = parts[0].strip()
            score_str = parts[1].replace(')', '').strip() if len(parts) > 1 else '0'
            try:
                score = float(score_str)
            except:
                score = 0.0
            if score >= threshold and name in GREETINGS:
                return name, score
    return 'unknown', 0.0

def generate_greeting(name, score=None):
    """根据身份生成问候语"""
    if name == '爹':
        return f'爹好！'
    elif name == '姐':
        return f'姐好！'
    elif name == '妈妈':
        return f'妈好呀！'
    else:
        score_str = f'({score:.2f})' if score else ''
        return f'您好{score_str}，请问是哪位？'

def process_voice_message(audio_path, original_text):
    """处理语音消息的完整流程"""
    name, score = recognize_speaker(audio_path)
    
    if name != 'unknown':
        greeting = generate_greeting(name, score)
        # 返回识别结果让AI处理
        return name, score, f"【声纹识别：{name}，置信度{score:.2%}】{greeting} "
    else:
        return 'unknown', score, f"【声纹识别：未知，最低分{score:.2f}】"

if __name__ == '__main__':
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        name, score, prefix = process_voice_message(audio_file, '')
        print(f'识别结果: {name} (得分: {score:.4f})')
