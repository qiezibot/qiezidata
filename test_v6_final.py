"""
voice_id_v6 最终分析
"""
import sys, os, json, shutil, random
sys.path.insert(0, '.')
from voice_id_v6 import register_speaker, recognize, extract_full_features, PROFILES_DIR
import numpy as np

# 先用今天的语音重新注册爹（全部156条）
dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
all_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
all_files = [os.path.join(dl, f) for f in all_files if f.endswith('.bin')]
print(f"总语音数: {len(all_files)}")

# 清空并重新注册
if os.path.exists(PROFILES_DIR):
    shutil.rmtree(PROFILES_DIR)
os.makedirs(PROFILES_DIR, exist_ok=True)

# 全部注册（154条都用来学习）
print("\n=== 注册 爹 (全部 {len(all_files)} 条) ===")
register_speaker('爹', all_files)

# 对所有语音做完整测试
print("\n=== 全量自识别测试 ===")
all_scores = []
for i, f in enumerate(all_files):
    name, score, details = recognize(f, threshold=0.1)
    all_scores.append(score)

all_scores = np.array(all_scores)
print(f"\n=== 统计 (n={len(all_scores)}) ===")
print(f"  mean={np.mean(all_scores):.4f}")
print(f"  std={np.std(all_scores):.4f}")
print(f"  min={np.min(all_scores):.4f}")
print(f"  max={np.max(all_scores):.4f}")
print(f"  Q1={np.percentile(all_scores, 25):.4f}")
print(f"  median={np.percentile(all_scores, 50):.4f}")
print(f"  Q3={np.percentile(all_scores, 75):.4f}")
print(f"  P5={np.percentile(all_scores, 5):.4f}")
print(f"  P95={np.percentile(all_scores, 95):.4f}")

# 低分分析：找出所有<0.70的
low_scores = [s for s in all_scores if s < 0.70]
print(f"\n低分占比 (<0.70): {len(low_scores)}/{len(all_scores)} = {100*len(low_scores)/len(all_scores):.1f}%")
low_scores2 = [s for s in all_scores if s < 0.60]
print(f"极低分占比 (<0.60): {len(low_scores2)}/{len(all_scores)} = {100*len(low_scores2)/len(all_scores):.1f}%")
