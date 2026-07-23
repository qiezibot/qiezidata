import sys, json, wave, os
from vosk import Model, KaldiRecognizer

os.environ['PYTHONIOENCODING'] = 'utf-8'
model = Model(r'C:\vosk-model-small-cn-0.22')
wf = wave.open(sys.argv[1], 'rb')
rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    rec.AcceptWaveform(data)

r = json.loads(rec.FinalResult())
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_stt_out.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(r.get('text', '(no speech)'))
