"""
声纹识别 v5 - VAD裁剪 + 分帧对比 + 特征标准化
核心改进:
  1. VAD (voice activity detection) 裁剪静音段
  2. 分帧级对比：把每段音频分成 N 帧，逐帧打分，取中位数/均值
  3. 特征标准化 (z-score)：学习全局特征分布，消除量纲差异
"""
import os, json, warnings
import numpy as np
import librosa
warnings.filterwarnings('ignore')

SR = 16000
PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'voice_profiles_v5')
os.makedirs(PROFILES_DIR, exist_ok=True)

def vad_trim(y, sr=SR, top_db=30, min_len_s=0.3):
    """VAD: 去掉静音段，只保留语音活动区域"""
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db, frame_length=2048, hop_length=512)
    if len(y_trimmed) < sr * min_len_s:
        return y  # 保留原音频
    return y_trimmed

def extract_frame_features(frame, sr=SR):
    """从单帧(约2秒)提取特征向量"""
    feats = []
    
    # 1. MFCC (20维 × 4统计量 = 80维)
    mfcc = librosa.feature.mfcc(y=frame, sr=sr, n_mfcc=20, n_fft=2048, hop_length=512)
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
    for M in [mfcc, mfcc_delta, mfcc_delta2]:
        feats.extend([
            np.mean(M, axis=1),
            np.std(M, axis=1),
            np.percentile(M, 25, axis=1),
            np.percentile(M, 75, axis=1),
        ])
    # 20 × 4 × 3 = 240维
    
    # 2. 基频 F0
    f0, voiced, _ = librosa.pyin(frame, fmin=65, fmax=400, sr=sr)
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) > 0:
        feats.append([np.mean(f0_clean), np.std(f0_clean), 
                     np.percentile(f0_clean, 10), np.percentile(f0_clean, 90),
                     np.min(f0_clean), np.max(f0_clean)])
        feats.append([len(f0_clean) / len(f0)])
    else:
        feats.append([0, 0, 0, 0, 0, 0])
        feats.append([0])
    # 7维
    
    # 3. 频谱特征
    for fname in ['spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff']:
        feat = getattr(librosa.feature, fname)(y=frame, sr=sr, n_fft=2048)
        feats.append([np.mean(feat), np.std(feat), np.percentile(feat, 25), np.percentile(feat, 75)])
    
    zcr = librosa.feature.zero_crossing_rate(frame, hop_length=512)
    feats.append([np.mean(zcr), np.std(zcr)])
    # 18维
    
    # 4. 梅尔频谱
    mel = librosa.feature.melspectrogram(y=frame, sr=sr, n_mels=40, n_fft=2048)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    feats.append([np.mean(mel_db), np.std(mel_db)])
    # 频段能量 (8 bands)
    for b in range(0, 40, 5):
        feats.append([np.mean(mel_db[b:b+5])])
    # 10维
    
    # 5. 能量包络
    rms = librosa.feature.rms(y=frame, hop_length=512)[0]
    voice_ratio = np.mean(rms > np.mean(rms) * 0.3)
    feats.append([voice_ratio])
    # 1维
    
    result = np.concatenate([np.array(f).flatten() for f in feats])
    return result

def extract_features_v5(audio_path, num_frames=3):
    """
    分帧提取特征:
    - VAD裁剪
    - 分成 num_frames 帧
    - 每帧独立提取特征
    - 返回所有帧特征列表
    """
    try:
        y, sr = librosa.load(audio_path, sr=SR, mono=True)
        if len(y) < SR * 0.3:
            return None, None
        
        # VAD裁剪
        y = vad_trim(y, sr)
        
        # 如果太短不分帧
        frame_len = len(y) // num_frames
        if frame_len < SR * 0.5:  # 每帧至少0.5秒
            frame_feats = [extract_frame_features(y)]
            return y, frame_feats
        
        frames = []
        for i in range(num_frames):
            start = i * frame_len
            end = start + frame_len if i < num_frames - 1 else len(y)
            frame = y[start:end]
            if len(frame) >= SR * 0.3:
                frames.append(frame)
        
        if not frames:
            return None, None
        
        frame_feats = [extract_frame_features(f) for f in frames]
        
        # 确保所有帧维度一致
        dims = [len(f) for f in frame_feats]
        if len(set(dims)) > 1:
            return None, None
        
        return y, frame_feats
        
    except Exception as e:
        print(f"特征提取失败: {e}")
        return None, None

def compute_score(emb_frames, profile_frames, norm_mean=None, norm_std=None):
    """
    综合评分: 多帧交叉对比
    emb_frames: [frame1_vec, frame2_vec, ...]
    profile_frames: [[s1_frame1, s1_frame2, ...], [s2_frame1, ...], ...]
    """
    # 标准化
    if norm_mean is not None and norm_std is not None:
        emb_frames = [(f - norm_mean) / (norm_std + 1e-10) for f in emb_frames]
        profile_frames = [[(f - norm_mean) / (norm_std + 1e-10) for f in s] for s in profile_frames]
    
    # 所有profile样本的所有帧
    all_profile_frames = [f for s in profile_frames for f in s]
    
    # 交叉对比
    scores = []
    for ef in emb_frames:
        ef_norm = ef / (np.linalg.norm(ef) + 1e-10)
        for pf in all_profile_frames:
            pf_norm = pf / (np.linalg.norm(pf) + 1e-10)
            scores.append(float(np.dot(ef_norm, pf_norm)))
    
    # 多帧聚合: 用中位数 + 均值
    median_score = np.median(scores)
    mean_score = np.mean(scores)
    
    # 最佳匹配帧得分
    best_frame_scores = []
    for ef in emb_frames:
        ef_norm = ef / (np.linalg.norm(ef) + 1e-10)
        frame_best = max(float(np.dot(ef_norm, pf / (np.linalg.norm(pf) + 1e-10))) for pf in all_profile_frames)
        best_frame_scores.append(frame_best)
    mean_best = np.mean(best_frame_scores)
    
    # 综合
    final = 0.4 * median_score + 0.3 * mean_score + 0.3 * mean_best
    
    return final, {
        "median": median_score,
        "mean": mean_score,
        "mean_best_frame": mean_best,
        "frame_scores": len(scores)
    }

def register_v5(name, audio_files):
    all_frames = []
    for f in audio_files:
        y, frame_feats = extract_features_v5(f)
        if frame_feats is not None:
            all_frames.append(frame_feats)
            print(f"  [{name}] {os.path.basename(f)}: {len(frame_feats)}帧 × {len(frame_feats[0])}维")
    
    if not all_frames:
        print("注册失败")
        return False
    
    # 保存完整的帧级特征
    profile = {
        "name": name,
        "samples_frames": [[f.tolist() for f in frames] for frames in all_frames],
        "num_samples": len(all_frames),
        "num_frames_per_sample": [len(f) for f in all_frames],
        "dim": len(all_frames[0][0])
    }
    
    with open(os.path.join(PROFILES_DIR, f"{name}.json"), 'w', encoding='utf-8') as fp:
        json.dump(profile, fp, ensure_ascii=False, indent=2)
    
    total_frames = sum(len(f) for f in all_frames)
    print(f"[OK] 注册: {name} ({len(all_frames)}段, {total_frames}帧, {len(all_frames[0][0])}维)")
    return True

def recognize_v5(audio_path, threshold=0.55):
    y, emb_frames = extract_features_v5(audio_path)
    if emb_frames is None:
        return "unknown", 0.0
    
    # 加载profiles
    profiles = {}
    for f in os.listdir(PROFILES_DIR):
        if f.endswith('.json'):
            with open(os.path.join(PROFILES_DIR, f), 'r', encoding='utf-8') as fp:
                profiles[f.replace('.json', '')] = json.load(fp)
    
    if not profiles:
        return "unknown", 0.0
    
    best_name = "unknown"
    best_score = -1
    
    for pname, profile in profiles.items():
        samples_frames = [np.array(s) for s in profile["samples_frames"]]
        score, details = compute_score(emb_frames, samples_frames)
        
        print(f"  {pname}: median={details['median']:.6f}, mean={details['mean']:.6f}, "
              f"best_frame={details['mean_best_frame']:.6f}, final={score:.6f}")
        
        if score > best_score:
            best_score = score
            best_name = pname
    
    if best_score < threshold:
        return "unknown", best_score
    return best_name, best_score

def compute_norm_params(profiles):
    """计算全局标准化参数"""
    all_feats = []
    for name, p in profiles.items():
        for s in p["samples_frames"]:
            for f in s:
                all_feats.append(f)
    all_feats = np.array(all_feats)
    return np.mean(all_feats, axis=0), np.std(all_feats, axis=0)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        sys.exit(1)
    action = sys.argv[1]
    if action == "register":
        register_v5(sys.argv[2], sys.argv[3:])
    elif action == "recognize":
        name, score = recognize_v5(sys.argv[2])
        print(f"\n结果: {name} (得分: {score:.6f})")
