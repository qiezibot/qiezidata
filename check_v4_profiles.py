import json
for name in ['爹','姐']:
    p = json.load(open(f'voice_profiles_v4/{name}.json', encoding='utf-8'))
    dim = p.get('dim', len(p['template']))
    print(f'{name}: {p["num_samples"]} samples, dim={dim}')
