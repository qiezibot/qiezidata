"""
声纹识别 v3 - 使用 speechbrain 深度学习模型
"""
import os, json, warnings
import numpy as np
import torch
warnings.filterwarnings('ignore')

VOICE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(VOICE_DIR, 'voice_profiles_v3')
os.makedirs(PROFILES_DIR, exist_ok=True)

MODEL_CACHE = None
SAMPLE_RATE = 16000

def _get_model():
    global MODEL_CACHE
    if MODEL_CACHE is None:
        from speechbrain.inference.speaker import EncoderClassifier
        print("加载speechbrain模型...")
        MODEL_CACHE = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=os.path.join(VOICE_DIR, "model_cache"),
            run_opts={"device": "cpu"}
        )
    return MODEL_CACHE

def extract_embedding(audio_path):
    """提取speaker embedding (192维向量)"""
    import torchaudio
    try:
        signal, sr = torchaudio.load(audio_path)
        if sr != SAMPLE_RATE:
            resampler = torchaudio.transforms.Resample(sr, SAMPLE_RATE)
            signal = resampler(signal)
        # 取至少1秒
        if signal.shape[1] < SAMPLE_RATE:
            # pad
            pad_len = SAMPLE_RATE - signal.shape[1]
            signal = torch.nn.functional.pad(signal, (0, pad_len))
        
        classifier = _get_model()
        embedding = classifier.encode_batch(signal)
        return embedding.squeeze().detach().numpy()
    except Exception as e:
        print(f"提取embedding失败: {e}")
        return None

def register_speaker_v3(name, audio_files):
    embeddings = []
    for f in audio_files:
        emb = extract_embedding(f)
        if emb is not None:
            embeddings.append(emb)
            print(f"  [{name}] 已处理: {os.path.basename(f)} -> dim={len(emb)}")
    
    if not embeddings:
        print(f"注册失败: 无有效embedding")
        return
    
    embeddings = np.array(embeddings)
    template = np.mean(embeddings, axis=0)
    
    profile = {
        "name": name,
        "template": template.tolist(),
        "samples": [e.tolist() for e in embeddings],
        "num_samples": len(embeddings)
    }
    
    with open(os.path.join(PROFILES_DIR, f"{name}.json"), 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 注册完成: {name} ({len(embeddings)}段)")

def recognize_v3(audio_path, threshold=0.5):
    emb = extract_embedding(audio_path)
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
        
        print(f"  {name}: score={cos_sim:.6f}")
        
        if cos_sim > best_score:
            best_score = cos_sim
            best_name = name
    
    if best_score < threshold:
        return "unknown", best_score
    
    return best_name, best_score

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: register <name> <files...> | recognize <file>")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "register":
        name = sys.argv[2]
        files = sys.argv[3:]
        register_speaker_v3(name, files)
    elif action == "recognize":
        name, score = recognize_v3(sys.argv[2])
        print(f"\n结果: {name} (得分: {score:.6f})")
