#!/usr/bin/env python
"""
WavLM声纹识别系统 (基于 microsoft/wavlm-base-plus-sv)
不依赖torchaudio，纯transformers + soundfile + scipy
"""
import os, sys, json, warnings
import numpy as np
import soundfile as sf
from scipy import signal as scipy_signal
import torch

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
warnings.filterwarnings('ignore')

from transformers import WavLMForXVector, AutoFeatureExtractor

# 模型单例
_model = None
_processor = None

def get_model():
    global _model, _processor
    if _model is None:
        _model = WavLMForXVector.from_pretrained('microsoft/wavlm-base-plus-sv')
        _processor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base-plus-sv')
        _model.eval()
    return _model, _processor

def load_audio(path, target_sr=16000):
    """加载音频，重采样到target_sr，返回(信号数组, 采样率)"""
    sig, sr = sf.read(path)
    if len(sig.shape) > 1:
        sig = np.mean(sig, axis=1)
    if sr != target_sr:
        target_len = int(len(sig) * target_sr / sr)
        sig = scipy_signal.resample(sig, target_len)
    return sig, target_sr

def get_embedding(audio_path):
    """从音频文件提取WavLM SV嵌入(512维L2归一化)"""
    model, processor = get_model()
    sig, sr = load_audio(audio_path)
    inputs = processor(sig, sampling_rate=sr, return_tensors='pt', padding=True)
    with torch.no_grad():
        emb = model(**inputs).embeddings.squeeze().numpy()
    emb = emb / (np.linalg.norm(emb) + 1e-10)
    return emb.tolist()

REGISTRY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_registry_wavlm.json')

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_registry(registry):
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

def enroll(name, audio_path):
    """注册一条语音样本"""
    abs_path = os.path.abspath(audio_path)
    if not os.path.exists(abs_path):
        return {"error": f"文件不存在: {abs_path}"}
    
    emb = get_embedding(abs_path)
    registry = load_registry()
    
    if name not in registry:
        registry[name] = {"files": [], "embeddings": []}
    
    registry[name]["files"].append(abs_path)
    registry[name]["embeddings"].append(emb)
    save_registry(registry)
    
    return {"name": name, "file": abs_path, "samples": len(registry[name]["files"])}

def enroll_batch(name, file_list):
    """批量注册"""
    results = {'success': 0, 'errors': []}
    for f in file_list:
        r = enroll(name, f)
        if 'error' in r:
            results['errors'].append(r['error'])
        else:
            results['success'] += 1
    return results

def identify(audio_path, threshold=0.5):
    """识别语音属于谁，返回排序结果"""
    abs_path = os.path.abspath(audio_path)
    if not os.path.exists(abs_path):
        return {"error": f"文件不存在: {abs_path}"}
    
    registry = load_registry()
    if not registry:
        return {"error": "注册库为空，请先注册语音样本"}
    
    test_emb = np.array(get_embedding(abs_path))
    
    results = []
    for name, data in registry.items():
        scores = []
        for ref_emb in data['embeddings']:
            score = float(np.dot(test_emb, np.array(ref_emb)))
            scores.append(score)
        results.append({
            'name': name,
            'score': round(float(np.mean(scores)), 4),
            'max_score': round(float(np.max(scores)), 4),
            'samples': len(scores)
        })
    
    results.sort(key=lambda x: x['max_score'], reverse=True)
    
    best = results[0]
    if best['max_score'] >= threshold:
        result = {
            'identified': best['name'],
            'confidence': best['max_score'],
            'all_results': results
        }
    else:
        result = {
            'identified': 'unknown',
            'confidence': 0,
            'all_results': results
        }
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法:")
        print("  识别: python voice_id_wavlm.py identify <音频文件> [threshold]")
        print("  注册: python voice_id_wavlm.py enroll <人名> <音频文件>")
        print("  批量注册: python voice_id_wavlm.py enroll_batch <人名> <文件1> <文件2> ...")
        print("  列表: python voice_id_wavlm.py list")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'identify':
        audio = sys.argv[2]
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        result = identify(audio, threshold)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == 'enroll':
        name = sys.argv[2]
        audio = sys.argv[3]
        result = enroll(name, audio)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == 'enroll_batch':
        name = sys.argv[2]
        files = sys.argv[3:]
        result = enroll_batch(name, files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == 'list':
        registry = load_registry()
        for name, data in registry.items():
            print(f"{name}: {len(data['files'])} 样本")
            for f in data['files']:
                print(f"  - {f}")
