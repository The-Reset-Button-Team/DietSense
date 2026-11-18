import json
import os
import base64
import re
import urllib.request
import urllib.parse

STEPS_DIR = r"C:\Users\Prasoon\.gemini\antigravity\brain\1e2c1de0-c534-4b4d-9d31-d05dc7966cb0\.system_generated\steps"
DOCS_STITCH_DIR = r"c:\Users\Prasoon\git prasoon\CP AND EDIs\DietSense\docs\stitch"
FRONTEND_STITCH_DIR = r"c:\Users\Prasoon\git prasoon\CP AND EDIs\DietSense\frontend\public\stitch"

os.makedirs(os.path.join(DOCS_STITCH_DIR, "screens"), exist_ok=True)
os.makedirs(os.path.join(DOCS_STITCH_DIR, "assets"), exist_ok=True)
os.makedirs(os.path.join(FRONTEND_STITCH_DIR, "screens"), exist_ok=True)
os.makedirs(os.path.join(FRONTEND_STITCH_DIR, "assets"), exist_ok=True)

# 1. Project metadata & Design System
with open(os.path.join(STEPS_DIR, "16", "output.txt"), "r", encoding="utf-8") as f:
    project_data = json.load(f)

with open(os.path.join(DOCS_STITCH_DIR, "project.json"), "w", encoding="utf-8") as f:
    json.dump(project_data, f, indent=2)

if "designTheme" in project_data and "designMd" in project_data["designTheme"]:
    design_md = project_data["designTheme"]["designMd"]
    with open(os.path.join(DOCS_STITCH_DIR, "design_system.md"), "w", encoding="utf-8") as f:
        f.write(design_md)
    print("Saved design_system.md")

# 2. Screens mapping
screens_config = [
    {
        "name": "todays_plan",
        "title": "Today's Plan — DietSense",
        "html_step": 28,
        "img_step": 32,
    },
    {
        "name": "progress_analytics",
        "title": "Progress & Analytics — DietSense",
        "html_step": 42,
        "img_step": 44,
    },
    {
        "name": "pantry_scanner",
        "title": "AI Pantry & Grocery Scanner — DietSense",
        "html_step": 46,
        "img_step": 48,
    },
    {
        "name": "profile_studio",
        "title": "Profile Studio & Biometrics — DietSense",
        "html_step": 50,
        "img_step": 52,
    },
]

all_html_content = {}

for sc in screens_config:
    # Read HTML
    with open(os.path.join(STEPS_DIR, str(sc["html_step"]), "output.txt"), "r", encoding="utf-8") as f:
        h_data = json.load(f)
        html = h_data.get("html", "")
        all_html_content[sc["name"]] = html
        
        # Save HTML
        with open(os.path.join(DOCS_STITCH_DIR, "screens", f"{sc['name']}.html"), "w", encoding="utf-8") as out:
            out.write(html)
        with open(os.path.join(FRONTEND_STITCH_DIR, "screens", f"{sc['name']}.html"), "w", encoding="utf-8") as out:
            out.write(html)
        print(f"Saved {sc['name']}.html ({len(html)} chars)")

    # Read Image
    with open(os.path.join(STEPS_DIR, str(sc["img_step"]), "output.txt"), "r", encoding="utf-8") as f:
        img_data = json.load(f)
        img_b64 = img_data.get("image", "")
        img_bytes = base64.b64decode(img_b64)
        
        # Save PNG
        with open(os.path.join(DOCS_STITCH_DIR, "screens", f"{sc['name']}.png"), "wb") as out:
            out.write(img_bytes)
        with open(os.path.join(FRONTEND_STITCH_DIR, "screens", f"{sc['name']}.png"), "wb") as out:
            out.write(img_bytes)
        print(f"Saved {sc['name']}.png ({len(img_bytes)} bytes)")

# 3. Read README and ARCHITECTURE
with open(os.path.join(STEPS_DIR, "56", "output.txt"), "r", encoding="utf-8") as f:
    readme_data = json.load(f)
    readme_md = readme_data.get("html", "")
    with open(os.path.join(DOCS_STITCH_DIR, "screens", "README.md"), "w", encoding="utf-8") as out:
        out.write(readme_md)
    print("Saved Stitch README.md")

arch_md = """# DietSense — Technical Architecture

## 1. System Overview

DietSense is an **offline-first, safety-anchored, evidence-based** adaptive meal planning and recommendation system.
All nutritional values originate exclusively from authoritative food composition tables (**USDA FoodData Central** and **ICMR-NIN / IFCT 2017**). The recommendation engine applies rule-based constraints and explainable scoring to ensure recommendations are safe, transparent, and auditable.
"""
# Note: we can read full ARCHITECTURE from earlier step if needed or save it
with open(os.path.join(DOCS_STITCH_DIR, "screens", "ARCHITECTURE.md"), "w", encoding="utf-8") as out:
    out.write(arch_md)

# 4. Extract hosted URLs (lh3.googleusercontent.com, etc.)
url_pattern = re.compile(r'https://lh3\.googleusercontent\.com/[^\s"\'\<\>]+')
found_urls = set()

for name, html in all_html_content.items():
    urls = url_pattern.findall(html)
    for u in urls:
        found_urls.add(u)

# Also check thumbnailScreenshot from project_data
if "thumbnailScreenshot" in project_data and "downloadUrl" in project_data["thumbnailScreenshot"]:
    found_urls.add(project_data["thumbnailScreenshot"]["downloadUrl"])

print(f"Found {len(found_urls)} unique hosted image URLs. Downloading...")

url_map = {}
for i, url in enumerate(sorted(found_urls)):
    # determine asset name
    ext = ".png"
    asset_name = f"stitch_asset_{i+1:02d}{ext}"
    target_docs = os.path.join(DOCS_STITCH_DIR, "assets", asset_name)
    target_fe = os.path.join(FRONTEND_STITCH_DIR, "assets", asset_name)
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as resp, open(target_docs, 'wb') as out_file:
            content = resp.read()
            out_file.write(content)
            with open(target_fe, 'wb') as fe_file:
                fe_file.write(content)
        url_map[url] = f"/stitch/assets/{asset_name}"
        print(f"Downloaded {asset_name} ({len(content)} bytes) from {url[:60]}...")
    except Exception as e:
        print(f"Failed to download {url[:60]}: {e}")

# Save url mapping
with open(os.path.join(DOCS_STITCH_DIR, "assets_map.json"), "w", encoding="utf-8") as f:
    json.dump(url_map, f, indent=2)

print("Export complete!")
