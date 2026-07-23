import sys, os, json, shutil
sys.path.insert(0, '.')
from voice_id_v5 import register_v5, recognize_v5, PROFILES_DIR

# 重设v5目录
if os.path.exists(PROFILES_DIR):
    shutil.rmtree(PROFILES_DIR)
os.makedirs(PROFILES_DIR, exist_ok=True)

dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
all_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
all_files = [os.path.join(dl, f) for f in all_files if f.endswith('.bin')]
print(f"总语音数: {len(all_files)}")

# 方案：用最老的10条注册"爹"（会话刚开始的肯定是爹）
# 用最新的6条也注册"爹"（实时对话的也是爹）
# 看看v5能不能区分"别人"

# 今天所有语音都是爹，没有姐
# 使用今天语音中的前10条注册爹
register_dad = all_files[:10]
print(f"\n用最早10条注册爹:")
register_v5('爹', register_dad)

# 测试剩下的
print(f"\n测试所有语音的爹相似度:")
for i, f in enumerate(all_files[10::15]):  # 每隔15条取一条
    name, score = recognize_v5(f)
    fname = os.path.basename(f)[:12]
    result = "SELF" if name == "爹" else "MISMATCH"
    print(f"  [{result:9s}] {fname}: score={score:.6f}")
