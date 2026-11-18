import json, os

with open('docs/stitch/assets_map.json', 'r') as f:
    url_map = json.load(f)

screens = ['todays_plan', 'progress_analytics', 'pantry_scanner', 'profile_studio']
for s in screens:
    path = f'docs/stitch/screens/{s}.html'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        for orig_url, local_asset in url_map.items():
            content = content.replace(orig_url, local_asset)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        # also update frontend/public/stitch/screens/
        fe_path = f'frontend/public/stitch/screens/{s}.html'
        with open(fe_path, 'w', encoding='utf-8') as f:
            f.write(content)
print("Updated HTML files with local asset links.")
