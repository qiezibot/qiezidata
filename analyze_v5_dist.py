import sys, os, json
sys.path.insert(0, '.')
from voice_id_v5 import extract_features_v5
import numpy as np

dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
all_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
all_files = [os.path.join(dl, f) for f in all_files if f.endswith('.bin')]

# 把所有语音的特征提取出来，计算帧间相似度分布
print("提取所有语音特征...")
all_feats = []
for f in all_files:
    _, frames = extract_features_v5(f)
    if frames is not None:
        all_feats.append(frames)

print(f"成功提取 {len(all_feats)}/{len(all_files)} 段语音特征")

# 计算帧间相似度矩阵（同一个人的语音应该自一致）
# 随机采样一些对比
import random
random.seed(42)

scores_same = []  # 同一条语音的帧间相似度
scores_diff = []  # 不同语音的帧间相似度

# 每条语音自己和自己比
for frames in all_feats[:50]:
    if len(frames) >= 2:
        for i in range(len(frames)):
            for j in range(i+1, len(frames)):
                fi = frames[i] / (np.linalg.norm(frames[i]) + 1e-10)
                fj = frames[j] / (np.linalg.norm(frames[j]) + 1e-10)
                scores_same.append(float(np.dot(fi, fj)))

# 不同语音之间比（取1000对随机组合）
pairs = 0
for _ in range(2000):
    i = random.randint(0, len(all_feats)-1)
    j = random.randint(0, len(all_feats)-1)
    if i == j: continue
    fi = all_feats[i][np.random.randint(len(all_feats[i]))]
    fj = all_feats[j][np.random.randint(len(all_feats[j]))]
    fi = fi / (np.linalg.norm(fi) + 1e-10)
    fj = fj / (np.linalg.norm(fj) + 1e-10)
    scores_diff.append(float(np.dot(fi, fj)))
    pairs += 1

print(f"\n=== 同人帧间相似度 (n={len(scores_same)}) ===")
print(f"  mean={np.mean(scores_same):.4f}, std={np.std(scores_same):.4f}")
print(f"  min={min(scores_same):.4f}, max={max(scores_same):.4f}")
s25 = np.percentile(scores_same, 25)
s75 = np.percentile(scores_same, 75)
print(f"  Q1={s25:.4f}, median={np.median(scores_same):.4f}, Q3={s75:.4f}")

print(f"\n=== 不同语音帧间相似度 (n={len(scores_diff)}) ===")
print(f"  mean={np.mean(scores_diff):.4f}, std={np.std(scores_diff):.4f}")
print(f"  min={min(scores_diff):.4f}, max={max(scores_diff):.4f}")
d25 = np.percentile(scores_diff, 25)
d75 = np.percentile(scores_diff, 75)
print(f"  Q1={d25:.4f}, median={np.median(scores_diff):.4f}, Q3={d75:.4f}")

# 建议阈值：取同人最低分和异人最高分的中间值（如果overlap很小）
overlap_min = max(min(scores_same), min(scores_diff))
overlap_max = min(max(scores_same), max(scores_diff))
if overlap_min < overlap_max:
    print(f"\n⚠️ 重叠区域: [{overlap_min:.4f}, {overlap_max:.4f}]")
    print(f"   建议阈值: {(overlap_min + overlap_max) / 2:.4f}")
else:
    print(f"\n✅ 无重叠! 同人最低={min(scores_same):.4f}, 异人最高={max(scores_diff):.4f}")
    print(f"   建议阈值: {(min(scores_same) + max(scores_diff)) / 2:.4f}")
