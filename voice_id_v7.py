"""
声纹识别 v7.1 - 多层特征融合版
取wav2vec2-base的 第6层(中) + 第12层(顶) + last_hidden_state 三组特征拼接
大幅提升说话人区分度
"""

import os, json, sys
import numpy as np
import soundfile as sf
from scipy import signal as scipy_signal
import torch

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "voice_registry_v7.json")

_model = None
_processor = None

def get_model():
    global _model, _processor
    if _model is None:
        from transformers import Wav2Vec2Model, Wav2Vec2FeatureExtractor
        model_name = "facebook/wav2vec2-base"
        _processor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        _model = Wav2Vec2Model.from_pretrained(model_name, output_hidden_states=True)
        _model.eval()
    return _model, _processor

def load_audio(path, target_sr=16000):
    sig, sr = sf.read(path)
    if len(sig.shape) > 1:
        sig = np.mean(sig, axis=1)
    if sr != target_sr:
        target_len = int(len(sig) * target_sr / sr)
        sig = scipy_signal.resample(sig, target_len)
    return sig, target_sr

def get_embedding(audio_path):
    """提取多层融合特征 (768+768+768=2304维)"""
    model, processor = get_model()
    sig, sr = load_audio(audio_path)
    
    inputs = processor(sig, sampling_rate=sr, return_tensors="pt", padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 取三组特征
    last_hidden = outputs.last_hidden_state  # [1, T, 768]
    hidden_states = outputs.hidden_states    # 13层 [1, T, 768]
    
    # 第6层（中间层）
    mid_layer = hidden_states[6]
    # 第12层（顶层）
    top_layer = hidden_states[12]
    
    # 各层mean pooling
    emb1 = last_hidden.mean(dim=1).squeeze().numpy()
    emb2 = mid_layer.mean(dim=1).squeeze().numpy()
    emb3 = top_layer.mean(dim=1).squeeze().numpy()
    
    # 拼接 + L2归一化
    emb = np.concatenate([emb1, emb2, emb3])
    emb = emb / np.linalg.norm(emb)
    return emb

def cosine_similarity(a, b):
    return float(np.dot(a, b))

def enroll(name, audio_path):
    registry = {}
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)
    
    emb = get_embedding(audio_path)
    
    if name not in registry:
        registry[name] = {"embeddings": [], "count": 0}
    
    registry[name]["embeddings"].append(emb.tolist())
    registry[name]["count"] += 1
    
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    print(f"OK:{name} ({registry[name]['count']}样本)")

def identify(audio_path):
    registry = {}
    if not os.path.exists(REGISTRY_FILE):
        print("ERROR: 无注册数据")
        return
    
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)
    
    emb = get_embedding(audio_path)
    
    results = {}
    for name, data in registry.items():
        scores = [cosine_similarity(emb, np.array(ref_emb)) for ref_emb in data["embeddings"]]
        results[name] = max(scores)
    
    sorted_results = sorted(results.items(), key=lambda x: -x[1])
    for name, score in sorted_results:
        print(f"  {name}={score:.4f}")
    
    best_name, best_score = sorted_results[0]
    threshold = 0.85
    if best_score < threshold:
        print(">> 陌生人")
    else:
        print(f">> {best_name}")

def list_users():
    if not os.path.exists(REGISTRY_FILE):
        print("无注册数据")
        return
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        registry = json.load(f)
    for name, data in registry.items():
        print(f"  {name}: {data['count']}样本")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python voice_id_v7.py [enroll|identify|list] [参数...]")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "enroll":
        if len(sys.argv) < 4:
            print("用法: python voice_id_v7.py enroll <姓名> <音频文件>")
            sys.exit(1)
        enroll(sys.argv[2], sys.argv[3])
    
    elif action == "identify":
        if len(sys.argv) < 3:
            print("用法: python voice_id_v7.py identify <音频文件>")
            sys.exit(1)
        identify(sys.argv[2])
    
    elif action == "list":
        list_users()
    
    else:
        print(f"未知操作: {action}")
