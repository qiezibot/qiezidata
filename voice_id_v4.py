"""
声纹识别 v4 - 使用更丰富的声学特征 + 多维度评分
主要改进：提取基频(F0)、共振峰(Formant)、能量包络等区分度高的特征
"""
import os, json, warnings
import numpy as np
import librosa
warnings.filterwarnings('ignore')

SR = 16000
PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'voice_profiles_v4')
os.makedirs(PROFILES_DIR, exist_ok=True)

def extract_features_v4(audio_path):
    """提取全方位声纹特征"""
    try:
        y, sr = librosa.load(audio_path, sr=SR, mono=True)
        if len(y) < SR * 0.3:
            return None
        
        feats = []
        
        # 1. MFCC (40维, delta, delta-delta)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40, n_fft=2048, hop_length=512)
        mfcc_delta = librosa.feature.delta(mfcc)
        mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
        
        for M in [mfcc, mfcc_delta, mfcc_delta2]:
            feats.extend([
                np.mean(M, axis=1),
                np.std(M, axis=1),
                np.percentile(M, 25, axis=1),
                np.percentile(M, 75, axis=1),
            ])
        # 共 40 * 4 * 3 = 480维
        
        # 2. 基频特征 (F0) - 男女区分度大
        f0, voiced, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr)
        f0_clean = f0[~np.isnan(f0)]
        if len(f0_clean) > 0:
            feats.append([np.mean(f0_clean), np.std(f0_clean), 
                         np.percentile(f0_clean, 10), np.percentile(f0_clean, 90),
                         np.min(f0_clean), np.max(f0_clean)])
            feats.append([len(f0_clean) / len(f0)])  # 有声比例
        else:
            feats.append([0, 0, 0, 0, 0, 0])
            feats.append([0])
        
        # 3. 频谱特征
        spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=2048)
        spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=2048)
        spec_roll = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=2048)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=512)
        
        for feat in [spec_cent, spec_bw, spec_roll, zcr]:
            feats.append([np.mean(feat), np.std(feat), np.percentile(feat, 25), np.percentile(feat, 75)])
        
        # 4. 梅尔频谱对比 (mel-scaled spectrogram)
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=80, n_fft=2048)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        feats.append([np.mean(mel_db), np.std(mel_db)])
        # 不同频段能量分布
        band_energy = []
        for band in range(0, 80, 10):
            band_energy.append(np.mean(mel_db[band:band+10]))
        feats.append(band_energy)
        
        # 5. 语音节奏特征 (语音段时长比例)
        rms = librosa.feature.rms(y=y, hop_length=512)
        voice_activity = (rms[0] > np.mean(rms[0]) * 0.3).astype(float)
        feats.append([np.mean(voice_activity)])
        
        # 6. 共振峰近似 (频谱包络峰值)
        spec = np.abs(librosa.stft(y, n_fft=2048))
        formant_approx = []
        for i in range(0, spec.shape[0], 20):
            formant_approx.append(np.mean(spec[i:i+20]))
        feats.append(formant_approx)
        
        # 汇总
        result = np.concatenate([np.array(f).flatten() for f in feats])
        return result
        
    except Exception as e:
        print(f"特征提取失败: {e}")
        return None

def register_v4(name, audio_files):
    embeddings = []
    for f in audio_files:
        emb = extract_features_v4(f)
        if emb is not None:
            embeddings.append(emb)
            print(f"  [{name}] {os.path.basename(f)}: {len(emb)}维")
    
    if not embeddings:
        print("注册失败")
        return False
    
    embeddings = np.array(embeddings)
    template = np.mean(embeddings, axis=0)
    
    profile = {
        "name": name,
        "template": template.tolist(),
        "samples": [e.tolist() for e in embeddings],
        "num_samples": len(embeddings),
        "dim": len(template)
    }
    
    with open(os.path.join(PROFILES_DIR, f"{name}.json"), 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 注册: {name} ({len(embeddings)}段, {len(template)}维)")
    return True

def recognize_v4(audio_path, threshold=0.65):
    emb = extract_features_v4(audio_path)
    if emb is None:
        return "unknown", 0.0
    
    # 加载profiles
    profiles = {}
    for f in os.listdir(PROFILES_DIR):
        if f.endswith('.json'):
            with open(os.path.join(PROFILES_DIR, f), 'r', encoding='utf-8') as fp:
                profiles[f.replace('.json', '')] = json.load(fp)
    
    if not profiles:
        return "unknown", 0.0
    
    emb_norm = emb / (np.linalg.norm(emb) + 1e-10)
    
    best_name = "unknown"
    best_score = -1
    
    for name, profile in profiles.items():
        template = np.array(profile["template"])
        template_norm = template / (np.linalg.norm(template) + 1e-10)
        cos_sim = float(np.dot(emb_norm, template_norm))
        
        # 额外：与所有样本的比较
        samples = np.array(profile["samples"])
        sample_sims = []
        for s in samples:
            s_norm = s / (np.linalg.norm(s) + 1e-10)
            sample_sims.append(float(np.dot(emb_norm, s_norm)))
        
        avg_sample = np.mean(sample_sims)
        min_sample = np.min(sample_sims)
        
        # 综合评分
        score = 0.5 * cos_sim + 0.3 * avg_sample + 0.2 * min_sample
        
        print(f"  {name}: cos={cos_sim:.6f}, avg={avg_sample:.6f}, min={min_sample:.6f}, final={score:.6f}")
        
        if score > best_score:
            best_score = score
            best_name = name
    
    if best_score < threshold:
        return "unknown", best_score
    return best_name, best_score

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit(1)
    action = sys.argv[1]
    if action == "register":
        register_v4(sys.argv[2], sys.argv[3:])
    elif action == "recognize":
        name, score = recognize_v4(sys.argv[2])
        print(f"\n结果: {name} (得分: {score:.6f})")
