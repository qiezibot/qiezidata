# voice_id_sb.py - 基于 speechbrain 的深度学习声纹识别
# python voice_id_sb.py enroll <名字> <语音文件.bin>
# python voice_id_sb.py identify <语音文件.bin>

import sys, os, json, subprocess, warnings
warnings.filterwarnings('ignore')

import torch
import numpy as np
import soundfile as sf

from speechbrain.inference.speaker import SpeakerRecognition

TMP_DIR = r'C:\temp\tts'
FFMPEG = r'C:\temp\ffmpeg.exe'
PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'voice_profiles')
os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

# 加载预训练模型（第一次会下载，之后缓存）
print('[INFO] 加载声纹模型...', file=sys.stderr)
try:
    verifier = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=os.path.join(os.path.dirname(__file__), 'pretrained_models', 'ecapa'),
        run_opts={"device": "cpu"}
    )
    print('[INFO] 模型加载完成', file=sys.stderr)
except Exception as e:
    print('[ERROR] 加载模型失败:', e, file=sys.stderr)
    sys.exit(1)

def bin_to_wav(bin_path, wav_path):
    subprocess.run([
        FFMPEG, '-y', '-i', bin_path,
        '-ar', '16000', '-ac', '1', '-sample_fmt', 's16',
        wav_path
    ], check=True, capture_output=True)

def get_embedding(wav_path):
    signal, sr = sf.read(wav_path)
    if sr != 16000:
        # 降采样
        import librosa
        signal = librosa.resample(signal, orig_sr=sr, target_sr=16000)
        sr = 16000
    # 至少1秒
    if len(signal) < 16000:
        repeats = int(np.ceil(16000 / len(signal)))
        signal = np.tile(signal, repeats)[:16000]
    # 取前3秒
    if len(signal) > 48000:
        signal = signal[:48000]
    signal_tensor = torch.tensor(signal).unsqueeze(0).float()
    with torch.no_grad():
        emb = verifier.encode_batch(signal_tensor)
    return emb.squeeze().numpy().tolist()

def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

def enroll(name, bin_path):
    tmp_wav = os.path.join(TMP_DIR, '_sb_enroll.wav')
    try:
        bin_to_wav(bin_path, tmp_wav)
        emb = get_embedding(tmp_wav)
        if emb is None:
            print('FAIL')
            return False
        
        profile_path = os.path.join(PROFILES_DIR, f'{name}_sb.json')
        samples = []
        if os.path.exists(profile_path):
            with open(profile_path, encoding='utf-8') as f:
                data = json.load(f)
                raw = data.get('samples', [data.get('embedding', [])])
                if raw and isinstance(raw[0], list):
                    samples = raw
                elif raw and isinstance(raw[0], (int, float)):
                    samples = [raw]
        
        samples.append(emb)
        avg_emb = np.mean(samples, axis=0).tolist()
        
        profile = {'name': name, 'embedding': avg_emb, 'samples': samples, 'count': len(samples)}
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False)
        print(f'OK:{name} ({len(samples)}样本)')
        return True
    except Exception as e:
        print(f'FAIL:{e}')
        return False
    finally:
        try: os.remove(tmp_wav)
        except: pass

def identify(bin_path, threshold=0.50):
    tmp_wav = os.path.join(TMP_DIR, '_sb_identify.wav')
    try:
        bin_to_wav(bin_path, tmp_wav)
        emb = get_embedding(tmp_wav)
        if emb is None:
            print('识别失败')
            return
        
        scores = {}
        for fname in os.listdir(PROFILES_DIR):
            if not fname.endswith('_sb.json'): continue
            with open(os.path.join(PROFILES_DIR, fname), encoding='utf-8') as f:
                profile = json.load(f)
            score = cosine_similarity(emb, profile['embedding'])
            scores[profile['name']] = score
        
        if not scores:
            print('陌生人')
            return
        
        best_name = max(scores, key=lambda k: scores[k])
        best_score = scores[best_name]
        
        # 输出分数（用于调试）
        for n, s in sorted(scores.items(), key=lambda x: -x[1]):
            print(f'DEBUG:{n}={s:.4f}', file=sys.stderr)
        
        if best_score < threshold:
            print('陌生人')
        else:
            print(best_name)
    except Exception as e:
        print(f'识别失败:{e}')
    finally:
        try: os.remove(tmp_wav)
        except: pass

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法:')
        print('  注册: python voice_id_sb.py enroll <名字> <语音文件>')
        print('  识别: python voice_id_sb.py identify <语音文件>')
        sys.exit(1)
    action = sys.argv[1]
    if action == 'enroll':
        enroll(sys.argv[2], sys.argv[3])
    elif action == 'identify':
        identify(sys.argv[2])
