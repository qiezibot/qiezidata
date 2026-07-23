import sys, json, wave, os, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from vosk import Model, KaldiRecognizer

model = Model(r'C:\vosk-model-small-cn-0.22')

while True:
    line = sys.stdin.readline()
    if not line:
        break
    path = line.strip()
    if not path:
        continue
    try:
        wf = wave.open(path, 'rb')
        rec = KaldiRecognizer(model, wf.getframerate())
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        r = json.loads(rec.FinalResult())
        text = r.get('text', '')
        sys.stdout.write(text + '\n')
        sys.stdout.flush()
        wf.close()
    except Exception as e:
        sys.stdout.write('(error: ' + str(e) + ')\n')
        sys.stdout.flush()
