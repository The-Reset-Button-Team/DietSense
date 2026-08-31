# DietSense — ETL Scripts (Member 4)

Python ETL pipeline for ingesting USDA FoodData Central and ICMR-NIN (IFCT 2017) datasets into PostgreSQL.

---

## Setup

```bash
cd scripts
pip install -r requirements.txt
cp ../.env.example .env    # fill in DATABASE_URL
```

---

## Pipeline — Run in Order

```
Phase 2 (Weeks 3–4):
1. etl_usda.py      → Parses USDA CSVs, normalizes to per-100g, outputs data/processed/usda_foods_normalized.csv
2. etl_ifct.py      → Extracts ICMR-NIN data from IFCT 2017 PDF, outputs data/processed/ifct_foods_normalized.csv
3. merge_sources.py → Deduplicates and merges both sources into data/processed/foods_merged.csv
4. load_db.py       → Bulk loads foods_merged.csv into PostgreSQL foods table
5. validate_data.py → Runs data quality assertions (no NaN calories, value bounds, row counts)
```

---

## Scripts (Phase 2 Implementation)

| Script | Description | Status |
|--------|-------------|--------|
| `etl_usda.py` | Parse USDA food.csv + food_nutrient.csv, map nutrient IDs to schema | Phase 2 |
| `etl_ifct.py` | Extract ICMR-NIN data from PDF via pdfplumber, map to schema | Phase 2 |
| `merge_sources.py` | Deduplicate across USDA and ICMR-NIN, prefer regional data for Indian foods | Phase 2 |
| `load_db.py` | SQLAlchemy bulk insert into `foods` table with conflict handling | Phase 2 |
| `validate_data.py` | Data quality checks — fail-fast if bounds violated | Phase 2 |

---

## Data Quality Rules

The safety gate in Phase 6 depends on this data being clean. Key assertions:

- `calories_kcal` must be > 0 and < 1000 per 100g
- `protein_g + carbohydrates_g + fat_g` must approximately sum to ≤ 100g
- No NULL values in: `name`, `data_source`, `external_id`, `calories_kcal`
- `allergen_flags` must be a valid PostgreSQL array (can be empty `{}`)
- No duplicate `(data_source, external_id)` pairs
