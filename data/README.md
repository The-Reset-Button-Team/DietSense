# DietSense — Data (Member 4)

Raw and processed nutrition datasets used by the ETL pipeline.

---

## Data Sources

| Source | Dataset | Format | Location |
|--------|---------|--------|----------|
| USDA | FoodData Central (April 2026) | CSV (extracted ZIP) | `database/` → ETL → `data/processed/` |
| ICMR-NIN | Indian Food Composition Tables 2017 (IFCT 2017) | PDF → extracted CSV | `database/IFCT2017.pdf` → `data/processed/` |
| WHO | Healthy Diet Fact Sheet | Reference only | `database/WHO_Healthy_Diet_Fact_Sheet.md` |

See [`sources.md`](sources.md) for detailed schema and normalization rules.

---

## Directory Structure

```
data/
├── raw/          # Original extracted files, never modified (gitignored)
├── processed/    # Cleaned, normalized, deduplicated CSVs ready for DB load (gitignored)
├── README.md     # This file
└── sources.md    # Data source documentation and normalization rules
```

> **Note**: `raw/` and `processed/` are gitignored — large CSV/PDF files are stored locally.
> The ETL scripts in `scripts/` produce the processed files from the `database/` source files.

---

## Phase 2 ETL Pipeline

Member 4 will implement the following scripts in `scripts/`:

1. `scripts/etl_usda.py` — Parse USDA `food.csv` + `food_nutrient.csv`, normalize units, deduplicate
2. `scripts/etl_ifct.py` — Extract ICMR-NIN data from IFCT 2017 PDF, map to schema
3. `scripts/load_db.py` — Load processed CSVs into PostgreSQL `foods` table
4. `scripts/validate_data.py` — Run data quality checks (no NaN calories, value bounds, etc.)

---

## Normalization Rules

All food data is normalized to **per 100g** before loading:
- Calories: kcal (not kJ — convert if needed: 1 kcal = 4.184 kJ)
- Macros: grams
- Sodium: milligrams
- Micronutrients: as specified per nutrient (mg or mcg)
