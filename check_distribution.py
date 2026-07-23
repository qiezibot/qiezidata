import sys, os, json
sys.path.insert(0, '.')
from voice_id_v4 import recognize_v4

dl = 'C:\\Users\\lfy20\\.openclaw\\media\\qqbot\\downloads\\1904006743\\CC26706F41E5B48C18ADF3C2A2AF86A0'
today_files = sorted(os.listdir(dl), key=lambda f: os.path.getmtime(os.path.join(dl, f)))
today_files = [os.path.join(dl, f) for f in today_files if f.endswith('.bin')]

# 用v4识别154条中的一部分（隔10条取一个），看分布
results = {'爹': 0, '姐': 0, 'unknown': 0}
for i, f in enumerate(today_files[::10]):  # 每隔10条取一条
    name, score = recognize_v4(f, threshold=0.4)
    results[name] = results.get(name, 0) + 1
    
print(f"v4识别分布（间隔采样共{len(today_files[::10])}条）:")
for k, v in results.items():
    print(f"  {k}: {v}")

# 看最早6条的识别结果（会话开始应该是爹）
print("\n最早6条语音的v4识别结果:")
for f in today_files[:6]:
    name, score = recognize_v4(f, threshold=0.4)
    fname = os.path.basename(f)[:12]
    print(f"  {fname}: {name} (score={score:.6f})")
