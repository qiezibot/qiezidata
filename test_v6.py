import sys, os, json, shutil
sys.path.insert(0, '.')
from voice_id_v6 import register_speaker, recognize, PROFILES_DIR

# 清空旧v6目录
if os.path.exists(PROFILES_DIR):
    shutil.rmtree(PROFILES_DIR)
os.makedirs(PROFILES_DIR, exist_ok=True)

dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
all_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
all_files = [os.path.join(dl, f) for f in all_files if f.endswith('.bin')]
print(f"总语音数: {len(all_files)}")

# 用最新的20条注册爹
print("\n=== 注册 爹 (最新20条) ===")
register_speaker('爹', all_files[-20:])

# 测试最早30条（不在注册集中）
print("\n=== 测试识别 (前30条，不在注册集) ===")
scores = []
for i, f in enumerate(all_files[:30]):
    name, score, details = recognize(f, threshold=0.1)
    fname = os.path.basename(f)[:12]
    tag = "SELF" if name == "爹" else "MIS"
    scores.append(score)
    print(f"  [{tag}] {fname}: {name} score={score:.6f}")

print(f"\n=== 统计 ===")
print(f"  爹得分: mean={np.mean(scores):.4f}, std={np.std(scores):.4f}")
print(f"  min={min(scores):.4f}, max={max(scores):.4f}")
print(f"  全部识别为爹: {sum(1 for s in scores if True)}/{len(scores)}")
