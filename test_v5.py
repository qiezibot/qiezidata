import sys, os, json, shutil
sys.path.insert(0, '.')
from voice_id_v5 import register_v5, recognize_v5, PROFILES_DIR

# 清空旧v5 profiles
if os.path.exists(PROFILES_DIR):
    shutil.rmtree(PROFILES_DIR)
os.makedirs(PROFILES_DIR, exist_ok=True)

dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
today_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
today_files = [os.path.join(dl, f) for f in today_files if f.endswith('.bin')]
print(f"共 {len(today_files)} 条语音（按时间排序）")

# 用最新的6条注册爹
register_files = today_files[-6:]
print("\n=== 注册 爹 (用最新6条) ===")
register_v5('爹', register_files)

# 测试识别前6条（最老的，不在注册集里）
print("\n=== 测试识别第1条（最早的，场景：爹说上线要问候）===")
name, score = recognize_v5(today_files[0])
print(f'结果: {name} (得分: {score:.6f})')

# 测试最新那条（在注册集里，但测试自一致性）
print(f"\n=== 测试识别第12条（最新 = 注册集里=爹） ===")
name, score = recognize_v5(today_files[-1])
print(f'结果: {name} (得分: {score:.6f})')
