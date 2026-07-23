import sys, json, wave, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from vosk import Model, KaldiRecognizer

model = Model(r'C:\vosk-model-small-cn-0.22')
wf = wave.open(sys.argv[1], 'rb')
rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    rec.AcceptWaveform(data)

r = json.loads(rec.FinalResult())
if r.get('text'):
    sys.stdout.write(r['text'])
else:
    sys.stdout.write('(no speech)')
