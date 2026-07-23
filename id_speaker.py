# 身份识别（独立脚本，绕开PowerShell编码问题）
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

import subprocess, librosa, numpy as np

bin_path = sys.argv[1]
tmp = r'C:\temp\tts\_id_last.wav'
subprocess.run([r'C:\temp\ffmpeg.exe', '-y', '-i', bin_path, '-ar', '16000', '-ac', '1', '-sample_fmt', 's16', tmp], check=True, capture_output=True)

signal, sr = librosa.load(tmp, sr=16000)
centroid = np.mean(librosa.feature.spectral_centroid(y=signal, sr=16000))
print(f'光谱质心: {centroid:.1f} Hz')
os.remove(tmp)

profiles_dir = os.path.join(os.path.dirname(__file__), 'voice_profiles')

# 1. 如果光谱质心明确 -> 直接判断
if centroid < 1700:
    print('性别: 男声 -> 爸爸')
    print('RESULT:爸爸')
    sys.exit(0)
elif centroid > 2100:
    print('性别: 女声 -> 妈妈或姐姐')
else:
    print('性别: 模糊区间(1700-2100Hz)')

# 2. 模糊区间用MFCC比对
mfcc_input = np.mean(librosa.feature.mfcc(y=signal, sr=16000, n_mfcc=13), axis=1)

results = []
for fname in os.listdir(profiles_dir):
    fpath = os.path.join(profiles_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        p = json.load(f)
    name = p['name']
    samples = p.get('samples', [])
    if not samples:
        continue
    best = 0
    for s in samples:
        a = np.array(mfcc_input)
        b = np.array(s)
        b = b.flatten()[:13] if b.ndim > 1 and len(b) >= 13 else b
        if len(b) != 13:
            continue
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
        if sim > best:
            best = sim
    results.append((name, best))
    print(f'  {name}: {best:.4f}')

if results:
    results.sort(key=lambda x: -x[1])
    best_name, best_score = results[0]
    print(f'RESULT:{best_name}')
else:
    print('RESULT:未知')
