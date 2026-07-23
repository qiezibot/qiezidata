# voice_id.py - 声纹识别 v4（光谱质心+MFCC双保险）
# -*- coding: utf-8 -*-
# 注册: python voice_id.py enroll <人物名> <语音文件.bin>
# 识别: python voice_id.py identify <语音文件.bin>

import sys, os, json, subprocess
import warnings
warnings.filterwarnings('ignore')

PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'voice_profiles')
FFMPEG = r'C:\temp\ffmpeg.exe'
TMP_DIR = r'C:\temp\tts'

os.makedirs(PROFILES_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

def bin_to_wav(bin_path, wav_path):
    subprocess.run([
        FFMPEG, '-y', '-i', bin_path,
        '-ar', '16000', '-ac', '1', '-sample_fmt', 's16',
        wav_path
    ], check=True, capture_output=True)

def get_embedding(audio_path):
    try:
        import librosa
        import numpy as np
        signal, sr = librosa.load(audio_path, sr=16000)
        if len(signal) < 16000:
            repeats = int(np.ceil(16000 / len(signal)))
            signal = np.tile(signal, repeats)[:16000]
        
        # 1. MFCC特征 (39维)
        mfcc = librosa.feature.mfcc(y=signal, sr=16000, n_mfcc=13)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)
        
        # 2. 光谱特征 - 男声女声区分关键
        centroid = librosa.feature.spectral_centroid(y=signal, sr=16000)  # 女声高
        rolloff = librosa.feature.spectral_rolloff(y=signal, sr=16000)    # 女声高
        bandwidth = librosa.feature.spectral_bandwidth(y=signal, sr=16000)
        zcr = librosa.feature.zero_crossing_rate(y=signal)
        
        features_list = []
        for feat in [mfcc, delta, delta2]:
            features_list.append(np.mean(feat, axis=1))
            features_list.append(np.std(feat, axis=1))
        
        for feat in [centroid, rolloff, bandwidth, zcr]:
            features_list.append(np.mean(feat, axis=1))
            features_list.append(np.std(feat, axis=1))
        
        emb = np.concatenate(features_list)
        emb = emb / (np.linalg.norm(emb) + 1e-10)
        return emb.tolist()
    except Exception as e:
        print('[ERROR] embedding:', e)
        return None

def cosine_similarity(a, b):
    import numpy as np
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

def get_gender_hint(audio_path):
    """通过光谱质心判断性别：男声低 < 1800Hz，女声高 > 2000Hz"""
    try:
        import librosa
        import numpy as np
        signal, sr = librosa.load(audio_path, sr=16000)
        if len(signal) < 16000:
            return None
        centroid = librosa.feature.spectral_centroid(y=signal, sr=16000)
        avg = float(np.mean(centroid))
        # 男声平均约1200-1800Hz，女声约2000-2800Hz
        if avg < 1700:
            return '男声'
        elif avg > 2100:
            return '女声'
        else:
            return None
    except:
        return None

def enroll(name, bin_path):
    tmp_wav = os.path.join(TMP_DIR, '_enroll_tmp.wav')
    try:
        bin_to_wav(bin_path, tmp_wav)
        emb = get_embedding(tmp_wav)
        if emb is None:
            print('FAIL: 无法提取声纹')
            return False
        
        profile_path = os.path.join(PROFILES_DIR, f'{name}.json')
        samples = []
        if os.path.exists(profile_path):
            with open(profile_path, encoding='utf-8') as f:
                data = json.load(f)
                raw_samples = data.get('samples', [data.get('embedding', [])])
                if raw_samples and isinstance(raw_samples[0], (list, tuple)):
                    samples = raw_samples
                elif raw_samples and isinstance(raw_samples[0], (int, float)):
                    samples = [raw_samples]
        
        samples.append(emb)
        import numpy as np
        avg_emb = np.mean(samples, axis=0).tolist()
        
        profile = {'name': name, 'embedding': avg_emb, 'samples': samples, 'count': len(samples)}
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, ensure_ascii=False)
        print(f'OK: {name} 声纹已注册（共{len(samples)}个样本）')
        return True
    except Exception as e:
        print(f'FAIL: {e}')
        return False
    finally:
        try: os.remove(tmp_wav)
        except: pass

def identify(bin_path, threshold=0.40):
    import numpy as np
    tmp_wav = os.path.join(TMP_DIR, '_identify_tmp.wav')
    try:
        bin_to_wav(bin_path, tmp_wav)
        
        # 性别预判
        gender = get_gender_hint(tmp_wav)
        
        emb = get_embedding(tmp_wav)
        if emb is None:
            return '未知'
        
        scores = {}
        for fname in os.listdir(PROFILES_DIR):
            if not fname.endswith('.json'): continue
            with open(os.path.join(PROFILES_DIR, fname), encoding='utf-8') as f:
                profile = json.load(f)
            score = cosine_similarity(emb, profile['embedding'])
            scores[profile['name']] = {'score': score, 'name': profile['name']}
        
        if not scores:
            return '陌生人'
        
        best_name = max(scores, key=lambda k: scores[k]['score'])
        best_score = scores[best_name]['score']
        
        # 如果性别预判明确，加强区分度
        if gender and best_score >= threshold:
            # 性别信息和声纹匹配一致才通过
            # 爹 = 男声，妈 = 女声（默认假设）
            if gender == '男声' and best_name == '爹':
                pass  # 匹配
            elif gender == '女声' and best_name == '妈':
                pass  # 匹配
            elif gender == '男声' and best_name == '妈':
                # 声纹说妈但听着像男声，备用：看看第二候选
                sorted_names = sorted(scores.keys(), key=lambda k: scores[k]['score'], reverse=True)
                if len(sorted_names) > 1:
                    second = scores[sorted_names[1]]
                    if second['score'] > threshold and sorted_names[1] == '爹':
                        return '爹'
            
            elif gender == '女声' and best_name == '爹':
                sorted_names = sorted(scores.keys(), key=lambda k: scores[k]['score'], reverse=True)
                if len(sorted_names) > 1:
                    second = scores[sorted_names[1]]
                    if second['score'] > threshold and sorted_names[1] == '妈':
                        return '妈'
        
        if best_score < threshold:
            return '陌生人'
        return best_name
    except Exception as e:
        return '识别失败'
    finally:
        try: os.remove(tmp_wav)
        except: pass

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法:')
        print('  注册: python voice_id.py enroll <名字> <语音文件>')
        print('  识别: python voice_id.py identify <语音文件>')
        sys.exit(1)
    action = sys.argv[1]
    if action == 'enroll':
        enroll(sys.argv[2], sys.argv[3])
    elif action == 'identify':
        print(identify(sys.argv[2]))
