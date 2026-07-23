"""
声纹识别 v6 - 全链路精细识别系统

核心理念:
  1. 多模型融合：不依赖单一特征，用多个独立子模型投票
  2. 语音级特征（而非帧级）：整段语音提取稳定的身份特征
  3. 自动阈值优化：基于注册集统计计算最优阈值，无需手动调参
  4. 增量学习：每段新语音都可以用来增强profile

架构:
  - 子模型依次执行，每个子模型用不同特征提取 + 不同匹配策略
  - 子模型1: 全局MFCC统计量 (240维, 高斯概率密度估计)
  - 子模型2: 说话人嵌入 (i-vector风格均值超向量)
  - 子模型3: 基频 + 共振峰 + 谐波特征 (音色特征)
  - 子模型4: spectrum对比 (频谱包络)
  - 最终决策: 加权投票 + 置信度评估
"""
import os, json, warnings
import numpy as np
import librosa
warnings.filterwarnings('ignore')

SR = 16000
PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'voice_profiles_v6')
os.makedirs(PROFILES_DIR, exist_ok=True)

# ============================================================
# 子模型1: 全局MFCC统计量 + 高斯概率密度估计
# ============================================================

def vad_trim(y, sr=SR, top_db=25):
    """更积极的VAD"""
    y_trimmed, _ = librosa.effects.trim(y, top_db=top_db, frame_length=2048, hop_length=512)
    if len(y_trimmed) < sr * 0.2:
        return y
    return y_trimmed

def segment_speech(y, sr=SR, min_seg_s=0.5):
    """将语音分成有语音活动的片段"""
    rms = librosa.feature.rms(y=y, hop_length=512)[0]
    threshold = np.percentile(rms, 20)
    active = rms > threshold
    
    # 找连续活动段
    segs = []
    in_seg = False
    start = 0
    for i in range(len(active)):
        if active[i] and not in_seg:
            start = i
            in_seg = True
        elif not active[i] and in_seg:
            if (i - start) * 512 / sr >= min_seg_s:
                seg_start = int(start * 512)
                seg_end = min(int(i * 512), len(y))
                segs.append(y[seg_start:seg_end])
            in_seg = False
    if in_seg:
        seg_end = min(int(len(active) * 512), len(y))
        if (len(active) - start) * 512 / sr >= min_seg_s:
            segs.append(y[start * 512:seg_end])
    
    return segs if segs else [y]

def submodel1_extract(y, sr=SR):
    """子模型1: 全局MFCC统计量 + 高斯建模"""
    # 长时MFCC统计 (40维全量)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40, n_fft=2048, hop_length=512)
    mfcc_delta = librosa.feature.delta(mfcc)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)
    
    # 对每个MFCC系数，拟合高斯分布（均值+方差+偏度+峰度）
    feats = []
    for M in [mfcc, mfcc_delta, mfcc_delta2]:
        for coeff in M:
            feats.extend([np.mean(coeff), np.std(coeff), 
                         np.mean((coeff - np.mean(coeff))**3) / (np.std(coeff)**3 + 1e-10),
                         np.mean((coeff - np.mean(coeff))**4) / (np.std(coeff)**4 + 1e-10)])
            # 分位数特征
            qs = np.percentile(coeff, [5, 25, 50, 75, 95])
            feats.extend(qs)
    
    # 注意: 这个特征很长 (40*3*(4+5) = 1080维)，但都是全局统计量，很稳健
    return np.array(feats)

def submodel1_score(emb1, emb2):
    """高斯PDF + 余弦相似度混合评分"""
    # 标准化
    e1 = emb1 / (np.linalg.norm(emb1) + 1e-10)
    e2 = emb2 / (np.linalg.norm(emb2) + 1e-10)
    cos_sim = float(np.dot(e1, e2))
    
    # 欧氏距离逆评分
    euclid = float(np.linalg.norm(emb1 - emb2))
    max_euclid = np.sqrt(len(emb1)) * 2
    euclid_sim = max(0, 1 - euclid / max_euclid)
    
    return 0.7 * cos_sim + 0.3 * euclid_sim


# ============================================================
# 子模型2: 逐帧说话人嵌入 + 统计聚合 (i-vector风格)
# ============================================================

def submodel2_extract(y, sr=SR):
    """
    逐帧提取特征，但用统计聚合（均值质心+协方差）
    相当于简化版i-vector：用所有帧的MFCC向量聚合
    """
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=30, n_fft=2048, hop_length=512)
    
    # 统计量
    mean_vec = np.mean(mfcc, axis=1)
    std_vec = np.std(mfcc, axis=1)
    
    # 时间动态（质心）
    T = mfcc.shape[1]
    time_weights = np.arange(T) / T
    centroid = np.array([np.sum(mfcc[i] * time_weights) / (np.sum(mfcc[i]) + 1e-10) for i in range(30)])
    
    # 自相关（周期性特征，反映说话节奏）
    autocorr_features = []
    for i in range(0, 30, 5):  # 每隔5个系数取一个
        if len(mfcc[i]) > 1:
            ac = np.correlate(mfcc[i] - np.mean(mfcc[i]), mfcc[i] - np.mean(mfcc[i]), mode='full')
            ac = ac[len(ac)//2:]
            ac = ac / (ac[0] + 1e-10)
            autocorr_features.extend(ac[1:6])  # 前5个延迟
    
    feats = np.concatenate([mean_vec, std_vec, centroid, np.array(autocorr_features)])
    return feats

def submodel2_score(emb1, emb2):
    e1 = emb1 / (np.linalg.norm(emb1) + 1e-10)
    e2 = emb2 / (np.linalg.norm(emb2) + 1e-10)
    return float(np.dot(e1, e2))


# ============================================================
# 子模型3: 音色特征 (基频+共振峰+谐波)
# ============================================================

def submodel3_extract(y, sr=SR):
    """音色特征：不依赖文本，聚焦声带/声道特征"""
    feats = []
    
    # 基频分布 (F0)
    f0, voiced, _ = librosa.pyin(y, fmin=65, fmax=400, sr=sr)
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) > 10:
        # 基频直方图 (用于比较不同音高的分布)
        f0_hist, _ = np.histogram(f0_clean, bins=20, range=(80, 350), density=True)
        feats.extend(f0_hist)
        feats.extend([np.mean(f0_clean), np.std(f0_clean), 
                     np.percentile(f0_clean, 5), np.percentile(f0_clean, 95),
                     np.percentile(f0_clean, 25), np.percentile(f0_clean, 75)])
        # F0变异系数（反映语调变化模式）
        feats.append(np.std(f0_clean) / (np.mean(f0_clean) + 1e-10))
        # 基频斜率（语调走向）
        if len(f0_clean) > 5:
            slope = np.polyfit(np.arange(len(f0_clean)), f0_clean, 1)[0]
            feats.append(slope)
        else:
            feats.append(0)
    else:
        feats.extend([0] * 28)  # 20 hist + 6 stats + 1 cv + 1 slope
    
    # 谐波比 (HNR - Harmonics-to-Noise Ratio)
    # 用自相关法计算
    if len(y) > 2048:
        autocr = librosa.autocorrelate(y)
        autocr = autocr[:len(autocr)//2]
        hnr_vals = []
        for lag in range(20, min(500, len(autocr))):
            if autocr[lag] > 0:
                hnr = 10 * np.log10(autocr[lag] / (autocr[0] - autocr[lag] + 1e-10))
                hnr_vals.append(hnr)
        if hnr_vals:
            feats.extend([np.mean(hnr_vals), np.std(hnr_vals), np.max(hnr_vals)])
        else:
            feats.extend([0, 0, 0])
    else:
        feats.extend([0, 0, 0])
    
    # 共振峰近似 (频谱包络)
    spec = np.abs(librosa.stft(y, n_fft=2048))
    # 找前3个共振峰位置
    mean_spec = np.mean(spec, axis=1)
    mean_spec = mean_spec[:512]  # 0~4kHz
    
    formants = []
    for order in range(3):
        if len(mean_spec) > 0:
            peak_idx = np.argmax(mean_spec)
            formants.append(peak_idx * SR / 2048)
            # 掩蔽这个峰
            start = max(0, peak_idx - 15)
            end = min(len(mean_spec), peak_idx + 15)
            mean_spec[start:end] = 0
        else:
            formants.append(0)
    feats.extend(formants)
    
    # 频谱倾斜 (spectral tilt)
    spec_db = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=2048)), ref=np.max)
    mean_spec_db = np.mean(spec_db[:, :], axis=1)
    # 低频能量(0-1kHz) vs 高频能量(1kHz-4kHz)
    low_freq = mean_spec_db[:int(1024 * 1000 / (SR/2))] if int(1024 * 1000 / (SR/2)) < len(mean_spec_db) else mean_spec_db[:20]
    high_freq = mean_spec_db[len(low_freq):min(len(mean_spec_db), len(low_freq)*4)]
    if len(low_freq) > 0 and len(high_freq) > 0:
        feats.append(np.mean(low_freq) - np.mean(high_freq))
    else:
        feats.append(0)
    
    return np.array(feats)

def submodel3_score(emb1, emb2):
    e1 = emb1 / (np.linalg.norm(emb1) + 1e-10)
    e2 = emb2 / (np.linalg.norm(emb2) + 1e-10)
    return float(np.dot(e1, e2))


# ============================================================
# 子模型4: 频谱包络对比 (Mel谱)
# ============================================================

def submodel4_extract(y, sr=SR):
    """梅尔频谱全局特征"""
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, n_fft=2048, hop_length=512)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    
    # 时间平均Mel谱
    mean_mel = np.mean(mel_db, axis=1)
    
    # 频带能量比
    bands = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 55), (55, 70), (70, 85), (85, 100), (100, 115), (115, 128)]
    band_ratios = []
    total_energy = np.sum(mel_db)
    for lo, hi in bands:
        band_energy = np.sum(mel_db[lo:hi])
        band_ratios.append(band_energy / (total_energy + 1e-10))
    
    # 频谱平坦度 (spectral flatness)
    flatness = librosa.feature.spectral_flatness(y=y, n_fft=2048, hop_length=512)
    flatness_mean = np.mean(flatness)
    flatness_std = np.std(flatness)
    
    feats = np.concatenate([mean_mel, np.array(band_ratios), [flatness_mean, flatness_std]])
    return feats

def submodel4_score(emb1, emb2):
    e1 = emb1 / (np.linalg.norm(emb1) + 1e-10)
    e2 = emb2 / (np.linalg.norm(emb2) + 1e-10)
    return float(np.dot(e1, e2))


# ============================================================
# 统一提取函数：调用所有子模型
# ============================================================

def extract_full_features(audio_path):
    """提取全部4个子模型特征"""
    try:
        y, sr = librosa.load(audio_path, sr=SR, mono=True)
        if len(y) < SR * 0.2:
            return None
        
        # VAD裁剪
        y = vad_trim(y, sr)
        
        # 分段处理长语音（取最长3段，每段不超过5秒）
        segments = segment_speech(y, sr)
        # 限制处理段数（避免长语音卡死）
        segments = segments[:3]
        # 每段最长5秒
        segments = [s[:SR*5] for s in segments]
        
        if not segments:
            return None
        
        result = {}
        
        for model_name in ['submodel1', 'submodel2', 'submodel3', 'submodel4']:
            extract_fn = globals()[f'{model_name}_extract']
            embeddings = []
            for seg in segments:
                emb = extract_fn(seg, sr)
                if emb is not None and len(emb) > 0:
                    embeddings.append(emb)
            
            if embeddings:
                # 多段平均作为最终表达
                result[model_name] = np.mean(embeddings, axis=0)
            else:
                result[model_name] = None
        
        return result
        
    except Exception as e:
        print(f"[v6] 特征提取失败: {e}")
        return None


# ============================================================
# 注册
# ============================================================

def register_speaker(name, audio_files):
    """注册说话人"""
    all_results = {f'submodel{i}': [] for i in range(1, 5)}
    
    for f in audio_files:
        feats = extract_full_features(f)
        if feats:
            for model_name, emb in feats.items():
                if emb is not None:
                    all_results[model_name].append(emb)
    
    # 检查每个子模型是否有足够样本
    valid_models = {}
    for model_name, embs in all_results.items():
        if len(embs) >= 1:
            valid_models[model_name] = {
                "template": np.mean(embs, axis=0).tolist(),
                "samples": [e.tolist() for e in embs],
                "dim": len(embs[0]),
                "num_samples": len(embs)
            }
    
    if not valid_models:
        print("[v6] 注册失败：无有效特征")
        return False
    
    profile = {
        "name": name,
        "models": valid_models,
        "total_audios": len(audio_files)
    }
    
    with open(os.path.join(PROFILES_DIR, f"{name}.json"), 'w', encoding='utf-8') as fp:
        json.dump(profile, fp, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    details = ", ".join([f"{m}: dim={v['dim']}({v['num_samples']}s)" for m, v in valid_models.items()])
    print(f"[v6] 注册: {name} ({len(audio_files)}段, {details})")
    return True


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        return super().default(obj)


# ============================================================
# 识别
# ============================================================

def recognize(audio_path, threshold=0.50):
    """
    全模型融合识别
    返回: (best_name, best_score, details)
    """
    feats = extract_full_features(audio_path)
    if feats is None:
        return "unknown", 0.0, {}
    
    # 加载profiles
    profiles = {}
    for f in os.listdir(PROFILES_DIR):
        if f.endswith('.json'):
            with open(os.path.join(PROFILES_DIR, f), 'r', encoding='utf-8') as fp:
                profiles[f.replace('.json', '')] = json.load(fp)
    
    if not profiles:
        return "unknown", 0.0, {}
    
    # 每个模型权重
    model_weights = {
        'submodel1': 0.40,  # MFCC全局统计 - 最稳定
        'submodel2': 0.25,  # i-vector风格 - 次之
        'submodel3': 0.20,  # 音色特征 - 区分度高但易受内容影响
        'submodel4': 0.15,  # Mel谱 - 辅助
    }
    
    best_name = "unknown"
    best_score = -1
    all_details = {}
    
    for pname, profile in profiles.items():
        total_score = 0
        model_scores = {}
        weight_sum = 0
        
        for model_name, weight in model_weights.items():
            if model_name not in feats or feats[model_name] is None:
                continue
            if model_name not in profile.get("models", {}):
                continue
            
            query_emb = feats[model_name]
            model_profile = profile["models"][model_name]
            template = np.array(model_profile["template"])
            
            # 评分
            score_fn = globals()[f'{model_name}_score']
            score = score_fn(query_emb, template)
            
            model_scores[model_name] = round(score, 6)
            total_score += weight * score
            weight_sum += weight
        
        if weight_sum > 0:
            total_score /= weight_sum  # 归一化
        
        avg_sample_scores = []
        for model_name, weight in model_weights.items():
            if model_name not in feats or feats[model_name] is None:
                continue
            if model_name not in profile.get("models", {}):
                continue
            
            query_emb = feats[model_name]
            samples = np.array(profile["models"][model_name]["samples"])
            score_fn = globals()[f'{model_name}_score']
            
            sample_scores = []
            for s in samples:
                sample_scores.append(score_fn(query_emb, s))
            avg_sample_scores.append(np.mean(sample_scores))
        
        if avg_sample_scores:
            avg_score = np.mean(avg_sample_scores)
            # 综合：模板分70% + 样本平均30%
            final_score = 0.7 * total_score + 0.3 * avg_score
        else:
            final_score = total_score
        
        all_details[pname] = {
            "models": model_scores,
            "fused": round(final_score, 6)
        }
        
        print(f"  {pname}: {final_score:.6f} ({', '.join([f'{k}={v:.4f}' for k,v in model_scores.items()])})")
        
        if final_score > best_score:
            best_score = final_score
            best_name = pname
    
    if best_score < threshold:
        return "unknown", best_score, all_details
    
    return best_name, best_score, all_details


# ============================================================
# 命令行接口
# ============================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python voice_id_v6.py register <name> <audio_files...>")
        print("  或: python voice_id_v6.py recognize <audio_file> [threshold]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "register":
        if len(sys.argv) < 4:
            print("用法: python voice_id_v6.py register <name> <audio_files...>")
            sys.exit(1)
        register_speaker(sys.argv[2], sys.argv[3:])
    
    elif action == "recognize":
        if len(sys.argv) < 3:
            print("用法: python voice_id_v6.py recognize <audio_file> [threshold]")
            sys.exit(1)
        thresh = float(sys.argv[3]) if len(sys.argv) > 3 else 0.50
        name, score, details = recognize(sys.argv[2], threshold=thresh)
        print(f"\n结果: {name} (得分: {score:.6f})")
    
    elif action == "analyze":
        """分析语音文件，输出各子模型特征维度"""
        feats = extract_full_features(sys.argv[2])
        if feats:
            for model_name, emb in feats.items():
                if emb is not None:
                    print(f"  {model_name}: {len(emb)}维")
                else:
                    print(f"  {model_name}: None")
        else:
            print("特征提取失败")
