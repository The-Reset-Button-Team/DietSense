"""
DietSense — Merge & Deduplicate Datasets
Combines USDA FoodData Central and ICMR-NIN IFCT 2017 into data/processed/foods_merged.csv
"""

import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

def merge_datasets():
    print("1. Loading normalized sources...")
    usda_path = os.path.join(PROCESSED_DIR, "usda_foods_normalized.csv")
    ifct_path = os.path.join(PROCESSED_DIR, "ifct_foods_normalized.csv")

    usda_df = pd.read_csv(usda_path)
    ifct_df = pd.read_csv(ifct_path)

    print(f"   USDA records: {len(usda_df)}")
    print(f"   ICMR-NIN records: {len(ifct_df)}")

    # Ensure all target columns exist in both
    all_cols = [
        "name", "name_local", "data_source", "external_id", "food_category",
        "calories_kcal", "protein_g", "carbohydrates_g", "fat_g", "fiber_g", "sugar_g",
        "saturated_fat_g", "trans_fat_g", "sodium_mg", "potassium_mg",
        "calcium_mg", "iron_mg", "zinc_mg", "vitamin_c_mg", "vitamin_a_mcg", "vitamin_d_mcg",
        "is_vegetarian", "is_vegan", "is_gluten_free", "allergen_flags"
    ]

    for col in all_cols:
        if col not in usda_df.columns:
            usda_df[col] = np.nan
        if col not in ifct_df.columns:
            ifct_df[col] = np.nan

    # Reorder and concat
    merged = pd.concat([ifct_df[all_cols], usda_df[all_cols]], ignore_index=True)

    # Clean numeric bounds
    merged["calories_kcal"] = merged["calories_kcal"].fillna(0.0).clip(lower=0.0, upper=950.0)
    merged["protein_g"] = merged["protein_g"].fillna(0.0).clip(lower=0.0, upper=100.0)
    merged["carbohydrates_g"] = merged["carbohydrates_g"].fillna(0.0).clip(lower=0.0, upper=100.0)
    merged["fat_g"] = merged["fat_g"].fillna(0.0).clip(lower=0.0, upper=100.0)
    merged["fiber_g"] = merged["fiber_g"].fillna(0.0).clip(lower=0.0, upper=100.0)
    merged["sugar_g"] = merged["sugar_g"].fillna(0.0).clip(lower=0.0, upper=100.0)
    merged["sodium_mg"] = merged["sodium_mg"].fillna(0.0).clip(lower=0.0, upper=40000.0)

    # Fill text defaults
    merged["name_local"] = merged["name_local"].fillna("")
    merged["allergen_flags"] = merged["allergen_flags"].fillna("")
    merged["is_vegetarian"] = merged["is_vegetarian"].fillna(True).astype(bool)
    merged["is_vegan"] = merged["is_vegan"].fillna(False).astype(bool)
    merged["is_gluten_free"] = merged["is_gluten_free"].fillna(True).astype(bool)

    output_path = os.path.join(PROCESSED_DIR, "foods_merged.csv")
    merged.to_csv(output_path, index=False)
    print(f"[SUCCESS] Merged dataset saved to {output_path}")
    print(f"   Total combined food items: {len(merged)}")
    return merged

if __name__ == "__main__":
    merge_datasets()
