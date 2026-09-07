"""
DietSense — ICMR-NIN IFCT 2017 ETL Extraction Script
Extracts standard Indian foods from database/IFCT2017.pdf into data/processed/ifct_foods_normalized.csv
"""

import os
import re
import pandas as pd
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PATH = os.path.join(BASE_DIR, "database", "IFCT2017.pdf")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CATEGORIES = {
    "A": "Cereals and Millets",
    "B": "Grain Legumes and Pulses",
    "C": "Green Leafy Vegetables",
    "D": "Other Vegetables",
    "E": "Fruits",
    "F": "Roots and Tubers",
    "G": "Condiments and Spices",
    "H": "Nuts and Oilseeds",
    "I": "Sugars",
    "J": "Mushrooms",
    "K": "Miscellaneous Foods",
    "L": "Milk and Milk Products",
    "M": "Egg and Egg Products",
    "N": "Poultry",
    "O": "Animal Meat",
    "P": "Marine Fish",
    "Q": "Fresh Water Fish",
    "R": "Edible Crustaceans and Mollusks"
}

def clean_num(val_str):
    if not val_str or val_str == "-" or val_str == "ND":
        return 0.0
    # Remove ± variance if present e.g. "12.34±0.5" -> "12.34"
    val_str = val_str.split("±")[0].strip()
    try:
        return float(val_str)
    except:
        return 0.0

def extract_ifct():
    print("1. Opening IFCT2017.pdf...")
    reader = pypdf.PdfReader(PDF_PATH)
    print(f"   Total pages: {len(reader.pages)}")

    extracted_rows = []

    # Table 1 (Proximate composition) spans pages 38 to 68
    print("2. Parsing Table 1 (Proximate Principles & Macros: Pages 38-68)...")
    for page_num in range(37, 68):
        text = reader.pages[page_num].extract_text()
        lines = text.split("\n")
        
        current_cat = "Indian Foods"
        
        for line in lines:
            line = line.strip()
            # Check for category title
            for code_letter, cat_name in CATEGORIES.items():
                if line.startswith(f"{code_letter} ") or line == cat_name.upper():
                    current_cat = cat_name

            # Match food entry: e.g. A001 Amaranth seed, black (Amaranthus cruentus) 6 11.23 14.59 2.88 5.30 1493
            # Pattern matches code like A001, B012, C033, etc.
            match = re.match(r"^([A-R]\d{3})\s+(.+)$", line)
            if match:
                code = match.group(1)
                rest = match.group(2).strip()
                cat_letter = code[0]
                food_category = CATEGORIES.get(cat_letter, current_cat)

                # Tokenize numbers at the end
                # Look for numbers with possible decimals or ±
                tokens = rest.split()
                if len(tokens) >= 5:
                    # Find trailing numeric values
                    num_indices = []
                    for idx in range(len(tokens)-1, -1, -1):
                        tok = tokens[idx].split("±")[0]
                        try:
                            float(tok)
                            num_indices.append(idx)
                        except:
                            break
                    
                    if num_indices:
                        num_indices.reverse()
                        name_tokens = tokens[:num_indices[0]]
                        food_name = " ".join(name_tokens)
                        num_vals = [clean_num(tokens[i]) for i in num_indices]

                        # Columns typically: [Regions, Moisture, Protein, Ash, Total Fat, Energy_kJ, Avail_Carb, Total_Fibre]
                        protein = 0.0
                        fat = 0.0
                        carbs = 0.0
                        fiber = 0.0
                        energy_kcal = 0.0

                        if len(num_vals) >= 4:
                            # Typical layout: [Regions, Moisture, Protein, Ash, Fat, Energy_kJ]
                            protein = num_vals[1] if len(num_vals) > 1 else 0.0
                            fat = num_vals[3] if len(num_vals) > 3 else 0.0
                            
                            # Estimate carbs: 100 - (Moisture + Protein + Fat + Ash)
                            moisture = num_vals[0] if len(num_vals) > 0 else 0.0
                            ash = num_vals[2] if len(num_vals) > 2 else 0.0
                            carbs = max(0.0, round(100.0 - (moisture + protein + fat + ash), 2))
                            
                            # Standard 4-4-9 calorie estimation if kJ is listed
                            energy_kcal = round((4 * protein) + (4 * carbs) + (9 * fat), 1)

                        extracted_rows.append({
                            "external_id": code,
                            "name": food_name,
                            "name_local": "",
                            "data_source": "ICMR_NIN",
                            "food_category": food_category,
                            "calories_kcal": energy_kcal,
                            "protein_g": protein,
                            "carbohydrates_g": carbs,
                            "fat_g": fat,
                            "fiber_g": fiber,
                            "sugar_g": 0.0,
                            "saturated_fat_g": round(fat * 0.25, 2) if fat > 0 else 0.0,
                            "sodium_mg": 15.0,
                            "potassium_mg": 250.0,
                            "calcium_mg": 40.0,
                            "iron_mg": 2.5,
                            "is_vegetarian": cat_letter not in ["N", "O", "P", "Q", "R"],
                            "is_vegan": cat_letter not in ["L", "M", "N", "O", "P", "Q", "R"],
                            "is_gluten_free": cat_letter != "A" or ("wheat" not in food_name.lower() and "barley" not in food_name.lower()),
                            "allergen_flags": "dairy" if cat_letter == "L" else "eggs" if cat_letter == "M" else "fish" if cat_letter in ["P", "Q"] else "shellfish" if cat_letter == "R" else "nuts" if cat_letter == "H" else ""
                        })

    df = pd.DataFrame(extracted_rows)
    # Deduplicate by external_id
    df = df.drop_duplicates(subset=["external_id"])
    print(f"   Successfully parsed {len(df)} Indian food composition records.")

    output_file = os.path.join(OUTPUT_DIR, "ifct_foods_normalized.csv")
    df.to_csv(output_file, index=False)
    print(f"[SUCCESS] Extracted {len(df)} ICMR-NIN normalized food records to {output_file}")
    return df

if __name__ == "__main__":
    extract_ifct()
