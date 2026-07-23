import sys, os, json, wave, struct, urllib.request, zipfile, shutil
from vosk import Model, KaldiRecognizer

# 下载模型
model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-small-cn-0.22")
if not os.path.exists(model_dir):
    zip_url = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip"
    zip_path = model_dir + ".zip"
    print("Downloading model...", flush=True)
    urllib.request.urlretrieve(zip_url, zip_path)
    print("Extracting...", flush=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(os.path.dirname(model_dir))
    os.remove(zip_path)

# 处理输入文件
input_file = sys.argv[1]
print(f"Input: {input_file}", flush=True)

# 如果是 .bin 文件，重命名为 .wav
if input_file.endswith('.bin'):
    wav_path = input_file + '.wav'
    shutil.copy(input_file, wav_path)
    input_file = wav_path

# 如果是 .wav，直接读取
if input_file.endswith('.wav'):
    try:
        wf = wave.open(input_file, "rb")
    except:
        # 可能是原始 PCM
        print("Trying as raw PCM...", flush=True)
        with open(input_file, 'rb') as f:
            raw_data = f.read()
        wav_path = input_file.replace('.wav', '_fixed.wav')
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(raw_data)
        wf = wave.open(wav_path, "rb")
else:
    # 可能是原始音频文件，当成 PCM 处理
    with open(input_file, 'rb') as f:
        raw_data = f.read()
    wav_path = input_file + '_pcm.wav'
    with wave.open(wav_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw_data)
    wf = wave.open(wav_path, "rb")

print(f"Channels: {wf.getnchannels()}, Rate: {wf.getframerate()}, Width: {wf.getsampwidth()}", flush=True)

# Vosk 识别
model = Model(model_dir)
rec = KaldiRecognizer(model, wf.getframerate())

results = []
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        r = json.loads(rec.Result())
        if r.get("text"):
            results.append(r["text"])

r = json.loads(rec.FinalResult())
if r.get("text"):
    results.append(r["text"])

output = "，".join(results) if results else "(no speech detected)"
print(f"TEXT:{output}", flush=True)
