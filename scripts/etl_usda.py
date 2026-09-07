"""
DietSense — USDA FoodData Central ETL Extraction Script
Extracts, cleans, and normalizes standard reference foods into data/processed/usda_foods_normalized.csv
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USDA_DIR = os.path.join(BASE_DIR, "database", "FoodData_Central_csv_2026-04-30", "FoodData_Central_csv_2026-04-30")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Standard Nutrient ID Mapping
NUTRIENT_MAP = {
    1008: "calories_kcal",      # Energy (kcal)
    2047: "calories_kcal_alt1", # Energy Atwater General
    2048: "calories_kcal_alt2", # Energy Atwater Specific
    1003: "protein_g",          # Protein (g)
    1004: "fat_g",              # Total lipid / Fat (g)
    1005: "carbohydrates_g",    # Carbohydrate (g)
    1079: "fiber_g",            # Total Dietary Fiber (g)
    2000: "sugar_g",            # Total Sugars (g)
    1258: "saturated_fat_g",    # Saturated fat (g)
    1257: "trans_fat_g",        # Trans fat (g)
    1093: "sodium_mg",          # Sodium (mg)
    1092: "potassium_mg",       # Potassium (mg)
    1087: "calcium_mg",         # Calcium (mg)
    1089: "iron_mg",            # Iron (mg)
    1095: "zinc_mg",            # Zinc (mg)
    1162: "vitamin_c_mg",       # Vitamin C (mg)
    1106: "vitamin_a_mcg",      # Vitamin A, RAE (mcg)
    1114: "vitamin_d_mcg",      # Vitamin D (mcg)
    1178: "vitamin_b12_mcg",    # Vitamin B-12 (mcg)
    1190: "folate_mcg"          # Folate (mcg)
}

def extract_usda():
    print("1. Loading USDA food.csv...")
    food_df = pd.read_csv(os.path.join(USDA_DIR, "food.csv"), low_memory=False)
    
    # Filter for standard high-quality nutrition reference items (Foundation, SR Legacy, Survey FNDDS)
    target_types = ["foundation_food", "sr_legacy_food", "survey_fndds_food"]
    food_df = food_df[food_df["data_type"].isin(target_types)].copy()
    print(f"   Selected {len(food_df)} reference food items ({', '.join(target_types)})")

    # Load categories
    print("2. Loading food categories...")
    cat_df = pd.read_csv(os.path.join(USDA_DIR, "food_category.csv"))
    cat_map = dict(zip(cat_df["id"], cat_df["description"]))
    food_df["food_category"] = food_df["food_category_id"].map(cat_map).fillna("Other")

    target_fdc_ids = set(food_df["fdc_id"])

    # Load nutrients
    print("3. Loading food_nutrient.csv (filtering relevant nutrient IDs)...")
    chunks = []
    chunksize = 250000
    for chunk in pd.read_csv(os.path.join(USDA_DIR, "food_nutrient.csv"), chunksize=chunksize, low_memory=False):
        filtered_chunk = chunk[chunk["fdc_id"].isin(target_fdc_ids) & chunk["nutrient_id"].isin(NUTRIENT_MAP.keys())]
        if not filtered_chunk.empty:
            chunks.append(filtered_chunk[["fdc_id", "nutrient_id", "amount"]])
    
    nutrient_df = pd.concat(chunks, ignore_index=True)
    print(f"   Found {len(nutrient_df)} nutrient data points.")

    # Pivot nutrients
    print("4. Pivoting nutrients to wide format...")
    nutrient_df["nutrient_col"] = nutrient_df["nutrient_id"].map(NUTRIENT_MAP)
    nutrient_df = nutrient_df.drop_duplicates(subset=["fdc_id", "nutrient_col"])
    pivoted = nutrient_df.pivot(index="fdc_id", columns="nutrient_col", values="amount").reset_index()

    # Merge with food info
    merged = pd.merge(food_df[["fdc_id", "description", "food_category"]], pivoted, on="fdc_id", how="left")

    # Clean calories column (fallback to Atwater if 1008 is missing)
    if "calories_kcal" not in merged.columns:
        merged["calories_kcal"] = np.nan
    if "calories_kcal_alt1" in merged.columns:
        merged["calories_kcal"] = merged["calories_kcal"].fillna(merged["calories_kcal_alt1"])
    if "calories_kcal_alt2" in merged.columns:
        merged["calories_kcal"] = merged["calories_kcal"].fillna(merged["calories_kcal_alt2"])

    for col in ["calories_kcal_alt1", "calories_kcal_alt2"]:
        if col in merged.columns:
            merged.drop(columns=[col], inplace=True)

    # Fill default values for missing numeric nutrients with 0.0
    for col in ["calories_kcal", "protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugar_g", "saturated_fat_g", "sodium_mg", "potassium_mg", "calcium_mg", "iron_mg"]:
        if col not in merged.columns:
            merged[col] = 0.0
        else:
            merged[col] = merged[col].fillna(0.0)

    # Rename columns to match DietSense PostgreSQL foods schema
    merged.rename(columns={
        "fdc_id": "external_id",
        "description": "name"
    }, inplace=True)

    merged["data_source"] = "USDA"
    merged["name_local"] = ""

    # Flag dietary tags
    def assign_flags(row):
        cat = str(row["food_category"]).lower()
        desc = str(row["name"]).lower()
        
        is_veg = not any(w in cat or w in desc for w in ["beef", "pork", "poultry", "chicken", "meat", "lamb", "veal", "fish", "finfish", "shellfish", "crustacean", "sausage", "bacon", "turkey", "duck"])
        is_vegan = is_veg and not any(w in cat or w in desc for w in ["dairy", "egg", "milk", "cheese", "butter", "yogurt", "ghee", "honey"])
        is_gf = not any(w in cat or w in desc for w in ["wheat", "barley", "rye", "flour", "bread", "pasta", "cookie", "cake", "biscuit"])

        allergens = []
        if any(w in cat or w in desc for w in ["nut", "seed", "peanut", "almond", "walnut", "cashew", "pistachio"]):
            allergens.append("nuts")
        if any(w in cat or w in desc for w in ["dairy", "milk", "cheese", "butter", "cream", "yogurt"]):
            allergens.append("dairy")
        if any(w in cat or w in desc for w in ["egg"]):
            allergens.append("eggs")
        if any(w in cat or w in desc for w in ["fish", "finfish"]):
            allergens.append("fish")
        if any(w in cat or w in desc for w in ["shellfish", "crustacean", "shrimp", "crab", "lobster"]):
            allergens.append("shellfish")
        if any(w in cat or w in desc for w in ["soy", "soya", "tofu"]):
            allergens.append("soy")
        if not is_gf:
            allergens.append("gluten")

        return pd.Series([is_veg, is_vegan, is_gf, ",".join(allergens)])

    print("5. Assigning vegetarian, vegan, allergen and dietary flags...")
    merged[["is_vegetarian", "is_vegan", "is_gluten_free", "allergen_flags"]] = merged.apply(assign_flags, axis=1)

    output_file = os.path.join(OUTPUT_DIR, "usda_foods_normalized.csv")
    merged.to_csv(output_file, index=False)
    print(f"[SUCCESS] Extracted {len(merged)} USDA normalized food records to {output_file}")
    return merged

if __name__ == "__main__":
    extract_usda()
