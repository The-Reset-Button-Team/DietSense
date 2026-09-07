"""
DietSense — Load Processed Foods into Database
Loads data/processed/foods_merged.csv into database/dietsense.db (SQLite)
"""

import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "foods_merged.csv")
DB_PATH = os.path.join(BASE_DIR, "database", "dietsense.db")

def load_foods():
    print("1. Reading foods_merged.csv...")
    df = pd.read_csv(CSV_PATH)
    print(f"   Total rows to load: {len(df)}")

    # Clean missing values
    df["name_local"] = df["name_local"].fillna("")
    df["allergen_flags"] = df["allergen_flags"].fillna("")
    df["food_category"] = df["food_category"].fillna("Other")

    for col in ["saturated_fat_g", "trans_fat_g", "potassium_mg", "calcium_mg", "iron_mg", "zinc_mg", "vitamin_c_mg", "vitamin_a_mcg", "vitamin_d_mcg"]:
        df[col] = df[col].fillna(0.0)

    print("2. Connecting to SQLite database...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_local TEXT,
        data_source TEXT NOT NULL,
        external_id TEXT NOT NULL,
        food_category TEXT NOT NULL,
        calories_kcal REAL NOT NULL,
        protein_g REAL NOT NULL,
        carbohydrates_g REAL NOT NULL,
        fat_g REAL NOT NULL,
        fiber_g REAL NOT NULL,
        sugar_g REAL NOT NULL,
        saturated_fat_g REAL,
        trans_fat_g REAL,
        sodium_mg REAL NOT NULL,
        potassium_mg REAL,
        calcium_mg REAL,
        iron_mg REAL,
        zinc_mg REAL,
        vitamin_c_mg REAL,
        vitamin_a_mcg REAL,
        vitamin_d_mcg REAL,
        is_vegetarian BOOLEAN NOT NULL,
        is_vegan BOOLEAN NOT NULL,
        is_gluten_free BOOLEAN NOT NULL,
        allergen_flags TEXT NOT NULL,
        UNIQUE(data_source, external_id)
    );
    """)

    print("3. Inserting records into foods table...")
    records = df.to_dict(orient="records")
    
    insert_sql = """
    INSERT OR REPLACE INTO foods (
        name, name_local, data_source, external_id, food_category,
        calories_kcal, protein_g, carbohydrates_g, fat_g, fiber_g, sugar_g,
        saturated_fat_g, trans_fat_g, sodium_mg, potassium_mg,
        calcium_mg, iron_mg, zinc_mg, vitamin_c_mg, vitamin_a_mcg, vitamin_d_mcg,
        is_vegetarian, is_vegan, is_gluten_free, allergen_flags
    ) VALUES (
        :name, :name_local, :data_source, :external_id, :food_category,
        :calories_kcal, :protein_g, :carbohydrates_g, :fat_g, :fiber_g, :sugar_g,
        :saturated_fat_g, :trans_fat_g, :sodium_mg, :potassium_mg,
        :calcium_mg, :iron_mg, :zinc_mg, :vitamin_c_mg, :vitamin_a_mcg, :vitamin_d_mcg,
        :is_vegetarian, :is_vegan, :is_gluten_free, :allergen_flags
    );
    """
    
    cur.executemany(insert_sql, records)
    conn.commit()

    count = cur.execute("SELECT COUNT(*) FROM foods").fetchone()[0]
    print(f"[SUCCESS] Loaded {count} food records into {DB_PATH}")
    conn.close()

if __name__ == "__main__":
    load_foods()
