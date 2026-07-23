import json, os
PROFILES_DIR = 'voice_profiles'
for fname in os.listdir(PROFILES_DIR):
    if not fname.endswith('.json'): continue
    with open(os.path.join(PROFILES_DIR, fname), encoding='utf-8') as f:
        p = json.load(f)
    print(f'{p["name"]}: {p["count"]} samples')
