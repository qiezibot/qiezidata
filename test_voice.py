import sys, os
# 把voice_id当模块导入测试
sys.stdout.reconfigure(encoding='utf-8')

tmp = os.path.expandvars(r'C:\temp\tts\_test.wav')
bin_path = os.path.expandvars(r'C:\Users\lfy20\.openclaw\qqbot\downloads\d965506218ff09050fb6ab442772da52.bin')

import subprocess
subprocess.run([
    r'C:\temp\ffmpeg.exe', '-y', '-i', bin_path,
    '-ar', '16000', '-ac', '1', '-sample_fmt', 's16',
    tmp
], check=True, capture_output=True)

import librosa, numpy as np
signal, sr = librosa.load(tmp, sr=16000)

# 光谱质心
centroid = np.mean(librosa.feature.spectral_centroid(y=signal, sr=16000))
print(f'光谱质心: {centroid:.1f} Hz', flush=True)
if centroid < 1700:
    print('性别判断: 男声（< 1700Hz）', flush=True)
elif centroid > 2100:
    print('性别判断: 女声（> 2100Hz）', flush=True)
else:
    print('性别判断: 模糊区间 (1700-2100Hz)', flush=True)

# MFCC
mfcc = librosa.feature.mfcc(y=signal, sr=16000, n_mfcc=13)
print(f'MFCC均值: {np.mean(mfcc):.3f}', flush=True)
print(f'信号长度: {len(signal)/16000:.1f}秒', flush=True)

os.remove(tmp)
