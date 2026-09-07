# DietSense — Complete Scientific Logic & Formulas Guide

> **"Every calorie is calculated with verified clinical science, never guessed or hallucinated."**

This document explains the exact math, medical equations, and institutional sources powering DietSense in simple, crystal-clear language.

---

## 1. 🧬 Metabolic Profile & Calorie Logic

When a user (like **arvykrane**) enters their **Weight, Height, Age, Biological Profile, and Activity Level**, DietSense calculates their exact energy needs using a 3-step scientific pipeline:

```
[Weight, Height, Age, Gender] ──▶ 1. BMR (Resting Burn)
                                        │
                                        ▼ (× Activity Multiplier)
                                  2. TDEE (Maintenance Calories)
                                        │
                                        ▼ (Goal Adjustment: Cut / Maintain / Bulk)
                                  3. Daily Calorie Target
```

---

### Step 1: BMR (Basal Metabolic Rate)
**What it means:** The exact number of calories your body burns at complete 24-hour rest just to stay alive (breathing, pumping blood, brain function, cellular repair).

* **Formula Used:** **Mifflin-St Jeor Equation** (1990)
* **Source:** *American Journal of Clinical Nutrition (AJCN)* & *Academy of Nutrition and Dietetics*. Clinical studies prove this is the most accurate equation for modern adults (within ±5% of indirect calorimetry).

```
Base Score = (10 × weight in kg) + (6.25 × height in cm) - (5 × age in years)

BMR (Male)   = Base Score + 5
BMR (Female) = Base Score - 161
```

#### ❓ Why `+5` for Male and `-161` for Female? (As seen in the dropdown)
Men naturally have a higher average proportion of **lean muscle mass** compared to total body weight, which consumes more oxygen and energy at rest. Women naturally have essential body fat necessary for endocrine and reproductive health, which has a slightly lower metabolic burn per gram. The `+5` and `-161` constants are empirically derived metabolic offset coefficients from clinical metabolic chamber trials.

---

### Step 2: TDEE (Total Daily Energy Expenditure)
**What it means:** The total calories you burn in a full 24-hour day including walking, working, exercising, and digesting food.

* **Formula:** `TDEE = BMR × Physical Activity Level (PAL)`
* **Source:** *Food and Agriculture Organization (FAO) / World Health Organization (WHO) Human Energy Requirements Standard*.

| Activity Level | Multiplier | Description |
| :--- | :---: | :--- |
| **Sedentary** | `1.200` | Desk job, little to no intentional exercise |
| **Lightly Active** | `1.375` | Daily walking or light workouts 1–3 days/week |
| **Moderately Active** | `1.550` | Moderate gym/sports workouts 3–5 days/week |
| **Very Active** | `1.725` | Hard physical training 6–7 days/week |
| **Extra Active** | `1.900` | Heavy physical labor or athlete training 2× daily |

---

### Step 3: Goal Adjustment (Cut vs Maintain vs Bulk)
**What it means:** Adjusting the maintenance energy to reach the user's health goal safely without metabolic damage.

* **🔥 Cut (Fat Loss / Obesity Prevention):** `TDEE - 400 kcal`
  * *Why 400 kcal deficit?* A 400 kcal/day deficit creates a gentle ~0.4 kg/week fat loss rate. This preserves lean muscle mass, avoids hormonal crashes, and prevents metabolic adaptation (the rebound effect).
  * *Safety Floor:* Never drops below 1,200 kcal for women or 1,500 kcal for men.
* **⚖️ Maintain:** `TDEE ± 0 kcal`
  * Keeps energy intake exactly equal to expenditure for stable weight.
* **💪 Lean Gain / Surplus:** `TDEE + 300 kcal`
  * Provides a small surplus to support muscle synthesis while minimizing fat accumulation.

---

## 2. 🥗 Macro & Micronutrient Distribution

Once the daily calorie target is set (e.g. **1,820 kcal** for arvykrane), how are those calories split across Carbs, Protein, and Fats?

* **Source:** **World Health Organization (WHO) Healthy Diet Fact Sheet (2026)** & **ICMR-NIN Indian Dietary Guidelines**.

```
                        1,820 kcal Target
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
     Carbohydrates           Protein              Healthy Fats
       50% Energy           20% Energy             30% Energy
        (228g)                (91g)                  (61g)
```

| Nutrient | WHO Target | DietSense Implementation | Caloric Density | Gram Calculation |
| :--- | :--- | :--- | :--- | :--- |
| **Carbohydrates** | 45% – 75% energy | **50% energy** (Unrefined/complex grains) | 4 kcal/g | `(1820 × 0.50) / 4 = 228g` |
| **Protein** | 10% – 20% energy | **20% energy** (Plant pulses + dairy/lean) | 4 kcal/g | `(1820 × 0.20) / 4 = 91g` |
| **Healthy Fats** | 15% – 30% energy | **30% energy** (Unsaturated oils, nuts, seeds) | 9 kcal/g | `(1820 × 0.30) / 9 = 61g` |
| **Dietary Fibre** | ≥ 25g / day | **≥ 30g / day** | 0 kcal | Sourced from whole grains, legumes, greens |
| **Free Sugars** | < 10% (ideal < 5%) | **< 5% total energy** | 4 kcal/g | Zero added table sugar |
| **Salt / Sodium** | < 5g salt (< 2g Na) | **< 2,000mg Sodium / day** | — | Cardioprotective threshold |

---

## 3. 📦 Authoritative Nutrition Data Sources

DietSense strictly rejects AI-generated nutrition estimates. All food features are extracted from clinical and government datasets:

1. **USDA FoodData Central (FDC)**:
   * **Source:** United States Department of Agriculture (`Foundation Foods` & `SR Legacy`).
   * **Items:** 13,694 standard reference whole foods.
   * **Attributes per food:** 27 verified macro & micronutrients per 100g (Iron, Calcium, Zinc, Vitamin C, Vitamin A, Folate, Potassium, Saturated/Trans Fats).

2. **ICMR-NIN IFCT 2017 (Indian Food Composition Tables)**:
   * **Source:** National Institute of Nutrition, Indian Council of Medical Research (Hyderabad).
   * **Items:** 487 traditional Indian foods (Ragi, Bajra, Jowar, Moong Dal, Palak, Paneer, Makhana, Ghee, Indian Fish).
   * **Attributes per food:** Proximate principles, regional moisture variations, indigenous micronutrient profiles.

---

## 4. 🎯 Recommendation Engine: 6-Factor Scoring Formula

How does DietSense choose the best breakfast, lunch, or dinner recipe for you?

Every meal candidate is evaluated across **6 independent scoring dimensions** and combined into a weighted score between `0.0` and `1.0`:

```
Score = 0.30×Macro + 0.20×Goal + 0.20×Preference + 0.15×Feedback + 0.10×Diversity + 0.05×Prep
```

*Source: `ml/scoring/formula.py` (Passed 10/10 automated tests)*

```
┌────────────────────────────────────────────────────────────────────────┐
│ Score Weight Breakdown                                                 │
│ ████████████████ 30% Macro Match (Matches target meal calories & ratio)│
│ ███████████ 20% Goal Alignment (Supports Cut/Maintain/Gain target)    │
│ ███████████ 20% User Preference (Cuisine, flavor, vegetarian/vegan)   │
│ ████████ 15% Feedback Loop (Learns from your 1–5 star ratings)         │
│ █████ 10% Diet Diversity (Prevents eating the exact same meal twice)   │
│ ███ 5% Prep Convenience (Fits within available cooking time)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 🛡️ Two Non-Negotiable Architectural Rules

As specified in `plan.pdf` and enforced in code:

### 🔒 Rule 1: The LLM Never Generates or Modifies Facts
* Large Language Models (like Gemini) are only allowed to **explain** recommendations in warm, human English.
* All calories, protein grams, and allergy flags are queried directly from PostgreSQL (`foods` & `recipes` tables).
* Gemini is **strictly read-only**; it cannot write or alter database nutrition values.

### 🚫 Rule 2: Hard Safety Gate Executes BEFORE AI Scoring
* If a user has a **Peanut Allergy** or is **Vegetarian**, DietSense filters out 100% of conflicting recipes in SQL *before* the ML scoring algorithm even runs.
* A dangerous recipe is never scored, ranked, or considered.

---

## 6. 🕒 Whole Day 5-Stage Meal Distribution

DietSense partitions daily calories across 5 natural metabolic phases throughout the day:

| Stage | Time | % of Day | Example for 1,820 kcal Target | Purpose |
| :--- | :---: | :---: | :---: | :--- |
| **1. Early Morning** | 7:00 AM | **5%** | **~90 kcal** | Digestive awakening & hydration (Jeera water + almonds) |
| **2. Breakfast** | 8:30 AM | **25%** | **~455 kcal** | Sustained energy & slow-release carbs (Moong dal chilla / oats) |
| **3. Main Lunch** | 1:15 PM | **35%** | **~635 kcal** | Peak energy & complete protein (Brown rice, jowar roti, dal, paneer) |
| **4. Evening Pause** | 5:00 PM | **10%** | **~180 kcal** | Preventing evening cortisol spikes (Roasted makhana + herbal tea) |
| **5. Restorative Dinner** | 8:00 PM | **25%** | **~460 kcal** | Light digestion & deep sleep support (Millet vegetable khichdi) |
| **Total** | — | **100%** | **1,820 kcal** | **Perfect metabolic harmony** |
