# DietSense — Data Sources Reference

## 1. USDA FoodData Central (April 2026)

- **URL**: https://fdc.nal.usda.gov/download-datasets.html
- **File**: `FoodData_Central_csv_2026-04-30.zip` (extracted to `database/FoodData_Central_csv_2026-04-30/`)
- **License**: Public Domain (US Government)
- **Key Files Used**:

| File | Description |
|------|-------------|
| `food.csv` | Master food list: `fdc_id`, `description`, `food_category_id`, `data_type` |
| `food_nutrient.csv` | Nutrient values per food: `fdc_id`, `nutrient_id`, `amount` |
| `nutrient.csv` | Nutrient definitions: `id`, `name`, `unit_name`, `nutrient_nbr` |
| `food_category.csv` | Food category lookup: `id`, `description` |
| `food_portion.csv` | Common portion sizes (reference only) |

- **ETL Script**: `scripts/etl_usda.py`
- **Output**: `data/processed/usda_foods_normalized.csv`

### Key USDA Nutrient IDs (mapped to schema columns)

| Nutrient | USDA Nutrient ID | Unit |
|----------|-----------------|------|
| Energy (Atwater) | 1008 | kcal |
| Protein | 1003 | g |
| Total Fat | 1004 | g |
| Carbohydrate | 1005 | g |
| Total Dietary Fiber | 1079 | g |
| Total Sugars | 2000 | g |
| Sodium | 1093 | mg |
| Potassium | 1092 | mg |
| Calcium | 1087 | mg |
| Iron | 1089 | mg |
| Vitamin C | 1162 | mg |
| Vitamin A (RAE) | 1106 | mcg |
| Vitamin D | 1114 | mcg |
| Vitamin B-12 | 1178 | mcg |
| Folate (DFE) | 1190 | mcg |
| Zinc | 1095 | mg |
| Saturated Fat | 1258 | g |
| Trans Fat | 1257 | g |

---

## 2. ICMR-NIN — Indian Food Composition Tables 2017 (IFCT 2017)

- **File**: `database/IFCT2017.pdf`
- **Publisher**: National Institute of Nutrition (NIN), Indian Council of Medical Research (ICMR)
- **Coverage**: ~528 Indian foods with full nutrient profiles
- **ETL Script**: `scripts/etl_ifct.py` (PDF text extraction + parsing)
- **Output**: `data/processed/ifct_foods_normalized.csv`

### IFCT Normalization Notes
- Values are per 100g edible portion
- Moisture content is provided but macros are on as-eaten basis
- Indian-specific foods (dal, roti, idli, etc.) will be tagged `data_source = ICMR_NIN`
- Map food groups to `food_category` schema field

---

## 3. WHO Healthy Diet Fact Sheet (Reference Only)

- **URL**: https://www.who.int/news-room/fact-sheets/detail/healthy-diet
- **Date**: 26 January 2026
- **File**: `database/WHO_Healthy_Diet_Fact_Sheet.md`
- **Use**: Dietary reference bounds used in `ml/scoring/formula.py`
  - Carbohydrates: 45–75% energy
  - Protein: 10–15% energy
  - Fat: 15–30% energy
  - Saturated fat: < 10% energy
  - Trans fat: < 1% energy
  - Salt: < 5 g/day
  - Fibre: ≥ 25 g/day
  - Fruit & Veg: ≥ 400 g/day

---

## Deduplication Strategy

When a food item exists in both USDA and ICMR-NIN:
1. Prefer ICMR-NIN for Indian foods (regional accuracy)
2. Prefer USDA for globally standardized foods
3. Flag duplicates with `name_local` field and keep both with distinct `external_id`
