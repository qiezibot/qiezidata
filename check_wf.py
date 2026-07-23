import json

with open(r'C:\ComfyUI\workflows\wedding_pro_codeformer.json') as f:
    wf = json.load(f)

for nid, node in wf.items():
    ct = node['class_type']
    if ct in ['UpscaleModelLoader', 'ImageUpscaleWithModel', 'ImageScaleBy', 'SaveImage', 'LoadImage']:
        print(f"{nid}: {ct}")
        print(f"  inputs: {json.dumps(node['inputs'], indent=4)}")
        print()
