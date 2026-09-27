"""
DietSense — Download Source Datasets for ETL Pipeline
Downloads USDA FoodData Central CSVs and IFCT 2017 PDF into the database/ directory.

This script is intended for CI and fresh-environment setup where the
gitignored database/ folder does not yet contain the raw source files.
"""

import os
import sys
import zipfile
import shutil
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")

# ---------------------------------------------------------------------------
# USDA FoodData Central (public domain, US Government)
# The ETL script (etl_usda.py) expects CSV files at:
#   database/FoodData_Central_csv_2026-04-30/FoodData_Central_csv_2026-04-30/
# We download the latest available bulk CSV release and place files there.
# ---------------------------------------------------------------------------
USDA_ZIP_URL = "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_csv_2024-10-31.zip"
USDA_ZIP_INNER_PREFIX = "FoodData_Central_csv_2024-10-31"
USDA_TARGET_DIR = os.path.join(
    DB_DIR,
    "FoodData_Central_csv_2026-04-30",
    "FoodData_Central_csv_2026-04-30",
)
USDA_NEEDED_FILES = ["food.csv", "food_nutrient.csv", "food_category.csv"]

# ---------------------------------------------------------------------------
# ICMR-NIN IFCT 2017 (Indian Food Composition Tables)
# Official PDF hosted by the National Institute of Nutrition.
# ---------------------------------------------------------------------------
IFCT_PDF_URLS = [
    "https://www.nin.res.in/ebooks/IFCT2017.pdf",
]
IFCT_PDF_PATH = os.path.join(DB_DIR, "IFCT2017.pdf")


def _download(url, dest, label="file"):
    """Download a URL to a local path with progress indication."""
    print(f"  Downloading {label}...")
    print(f"    URL:  {url}")
    print(f"    Dest: {dest}")
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as exc:
        print(f"    FAILED: {exc}")
        raise
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"    OK ({size_mb:.1f} MB)")


def download_usda():
    """Download and extract the three USDA CSV files needed by etl_usda.py."""
    os.makedirs(USDA_TARGET_DIR, exist_ok=True)

    # Skip if already present
    if all(os.path.exists(os.path.join(USDA_TARGET_DIR, f)) for f in USDA_NEEDED_FILES):
        print("[USDA] Source CSVs already present — skipping download.")
        return

    print("[USDA] Downloading FoodData Central bulk CSV archive...")
    zip_path = os.path.join(DB_DIR, "usda_fdc_temp.zip")
    _download(USDA_ZIP_URL, zip_path, "USDA FoodData Central ZIP")

    print("[USDA] Extracting required CSV files...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        for needed in USDA_NEEDED_FILES:
            member = f"{USDA_ZIP_INNER_PREFIX}/{needed}"
            target = os.path.join(USDA_TARGET_DIR, needed)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            size_mb = os.path.getsize(target) / (1024 * 1024)
            print(f"    Extracted {needed} ({size_mb:.1f} MB)")

    # Remove the large zip to free disk space
    os.remove(zip_path)
    print("[USDA] Done.\n")


def download_ifct():
    """Download the IFCT 2017 PDF needed by etl_ifct.py."""
    os.makedirs(DB_DIR, exist_ok=True)

    if os.path.exists(IFCT_PDF_PATH):
        print("[IFCT] PDF already present — skipping download.")
        return

    print("[IFCT] Downloading IFCT 2017 PDF...")
    last_err = None
    for url in IFCT_PDF_URLS:
        try:
            _download(url, IFCT_PDF_PATH, "IFCT 2017 PDF")
            print("[IFCT] Done.\n")
            return
        except Exception as exc:
            last_err = exc
            continue

    print(f"[IFCT] ERROR: Could not download IFCT 2017 PDF from any source.")
    raise last_err


def main():
    print("=" * 60)
    print("DietSense — Source Data Downloader")
    print("=" * 60 + "\n")

    download_usda()
    download_ifct()

    print("=" * 60)
    print("[SUCCESS] All source data downloaded and ready for ETL.")
    print("=" * 60)


if __name__ == "__main__":
    main()
