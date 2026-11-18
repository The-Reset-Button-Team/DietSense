import json, re

with open('docs/stitch/assets_map.json', 'r') as f:
    url_map = json.load(f)

screens = ['todays_plan', 'progress_analytics', 'pantry_scanner', 'profile_studio']
for s in screens:
    path = f'docs/stitch/screens/{s}.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f'=== {s} ===')
    for orig_url, local_asset in url_map.items():
        if orig_url in content:
            idx = content.find(orig_url)
            snippet = content[max(0, idx-120):min(len(content), idx+200)]
            alt_m = re.search(r'alt="([^"]+)"|data-alt="([^"]+)"', snippet)
            alt = alt_m.group(1) or alt_m.group(2) if alt_m else 'No alt'
            print(f'  {local_asset} -> {alt[:80]}')
