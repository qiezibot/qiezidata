"""
声纹识别系统 - 改进版
使用更丰富的特征 + 多段语音模板匹配
"""
import os
import json
import numpy as np
import librosa
import warnings
warnings.filterwarnings('ignore')

VOICE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(VOICE_DIR, 'voice_profiles')
os.makedirs(PROFILES_DIR, exist_ok=True)

# 采样配置
SR = 16000
N_MFCC = 20  # 更多MFCC系数
N_FFT = 2048
HOP_LENGTH = 512

def extract_features(audio_path, sr=SR):
    """提取更丰富的声纹特征"""
    try:
        y, sr_in = librosa.load(audio_path, sr=sr, mono=True)
        if len(y) < sr * 0.5:  # 少于0.5秒
            return None
        
        # 1. MFCC特征
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP_LENGTH)
        
        # 2. 光谱特征
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=HOP_LENGTH)
        
        # 3. 基频特征 (F0)
        f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), 
                                          fmax=librosa.note_to_hz('C7'), sr=sr)
        f0 = np.nan_to_num(f0, nan=0.0)
        
        # 汇总特征
        features = []
        
        # MFCC统计量 (均值 + 标准差 + 偏度)
        for i in range(mfcc.shape[0]):
            features.extend([
                np.mean(mfcc[i]),
                np.std(mfcc[i]),
                np.percentile(mfcc[i], 25),
                np.percentile(mfcc[i], 75),
            ])
        
        # 光谱特征统计
        for feat in [spectral_centroid, spectral_rolloff, spectral_bandwidth, zcr]:
            features.extend([
                np.mean(feat),
                np.std(feat),
            ])
        
        # F0特征
        voiced_f0 = f0[voiced_flag]
        if len(voiced_f0) > 0:
            features.extend([np.mean(voiced_f0), np.std(voiced_f0)])
        else:
            features.extend([0.0, 0.0])
        
        # 时长特征
        features.append(len(y) / sr)
        
        return np.array(features)
    except Exception as e:
        print(f"提取特征失败: {e}")
        return None


def register_speaker(name, audio_files, sr=SR):
    """注册说话人声音"""
    all_features = []
    for audio_file in audio_files:
        feat = extract_features(audio_file, sr)
        if feat is not None:
            all_features.append(feat)
    
    if not all_features:
        print(f"没有成功提取特征")
        return None, False
    
    # 计算总模板（均值）和每个样本
    all_features = np.array(all_features)
    template = np.mean(all_features, axis=0)
    
    profile = {
        "name": name,
        "template": template.tolist(),
        "samples": all_features.tolist(),
        "num_samples": len(all_features)
    }
    
    profile_path = os.path.join(PROFILES_DIR, f"{name}.json")
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] Registered: {name} ({len(all_features)} samples)")
    return profile, True


def recognize(audio_path, threshold=0.5, sr=SR):
    """识别说话人"""
    feat = extract_features(audio_path, sr)
    if feat is None:
        return "unknown", 0.0
    
    # 加载所有已注册的说话人
    profiles = {}
    for f in os.listdir(PROFILES_DIR):
        if f.endswith('.json'):
            with open(os.path.join(PROFILES_DIR, f), 'r', encoding='utf-8') as fp:
                data = json.load(fp)
                profiles[f.replace('.json', '')] = data
    
    if not profiles:
        return "unknown", 0.0
    
    best_name = "unknown"
    best_score = -1
    
    for name, profile in profiles.items():
        # 兼容新旧格式 (template / embedding)
        template_key = 'template' if 'template' in profile else 'embedding'
        template = np.array(profile[template_key], dtype=np.float64)
        
        # 维度不匹配的跳过（旧版本和新版本特征维度不同）
        if len(template) != len(feat):
            print(f"  {name}: 跳过 (维度不匹配: {len(template)} vs {len(feat)})")
            continue
        
        samples_key = 'samples' if 'samples' in profile else 'samples'
        samples_data = profile.get('samples', [profile[template_key]])
        # 过滤维度匹配的样本
        samples = np.array([s for s in samples_data if len(s) == len(feat)], dtype=np.float64)
        if len(samples) == 0:
            samples = np.array([template])
        
        # 余弦相似度
        template_norm = template / (np.linalg.norm(template) + 1e-10)
        feat_norm = feat / (np.linalg.norm(feat) + 1e-10)
        cos_sim = np.dot(template_norm, feat_norm)
        
        # 与所有样本的最小距离
        sample_sims = []
        for sample in samples:
            sample = np.array(sample)
            sample_norm = sample / (np.linalg.norm(sample) + 1e-10)
            sim = np.dot(sample_norm, feat_norm)
            sample_sims.append(sim)
        
        avg_sample_sim = np.mean(sample_sims)
        min_sample_sim = np.min(sample_sims)
        
        # 综合得分
        score = 0.6 * cos_sim + 0.3 * avg_sample_sim + 0.1 * min_sample_sim
        
        print(f"  {name}: cos={cos_sim:.4f}, avg={avg_sample_sim:.4f}, min={min_sample_sim:.4f}, final={score:.4f}")
        
        if score > best_score:
            best_score = score
            best_name = name
    
    if best_score < threshold:
        return "unknown", best_score
    
    return best_name, best_score


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  注册: python voice_id.py register <姓名> <语音文件1> [语音文件2 ...]")
        print("  识别: python voice_id.py recognize <语音文件>")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "register":
        if len(sys.argv) < 4:
            print("请提供姓名和至少一个语音文件")
            sys.exit(1)
        name = sys.argv[2]
        files = sys.argv[3:]
        register_speaker(name, files)
        
    elif action == "recognize":
        if len(sys.argv) < 3:
            print("请提供语音文件路径")
            sys.exit(1)
        audio_file = sys.argv[2]
        name, score = recognize(audio_file)
        print(f"\n识别结果: {name} (得分: {score:.4f})")
        
    elif action == "batch_register":
        # 批量处理：把所有.wav/.bin文件注册
        pass
