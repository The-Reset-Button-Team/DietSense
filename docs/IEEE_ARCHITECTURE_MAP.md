# DietSense: IEEE-Style System Architecture Map

> **Reference Document**: [`docs/ieee_system_architecture.html`](ieee_system_architecture.html)

---

## 🏛️ IEEE Block Diagram (Layered Architectural Pipeline)

```
+========================================================================================+
|                        LAYER 1: DATA INGESTION & USER ACQUISITION                      |
+------------------------------------+-----------------------------+---------------------+
| 1.1 Biometrics & Target Goal       | 1.2 Solo Routine Matrix     | 1.3 Vision OCR Ingestion
| - Weight (kg), Height (cm), Age   | - Meal Frequency (2/3/4/5)  | - Supermarket Receipt Slips
| - Sex, Activity Level (1.2 - 1.9x)| - Weekday Effort (Low/Mod)  | - Delivery Bills (Blinkit)
| - Goal: Cut (-400) / Surplus (+300)| - 1-Person Portion Scaling  | - Fridge Camera Snapshots
+------------------------------------+-----------------------------+---------------------+
                                            |
                                            v  [Structured Inputs & In-Stock Inventory]
+========================================================================================+
|                    LAYER 2: KNOWLEDGE BASE & HARD SAFETY FILTERING                     |
+--------------------------------------------------+-------------------------------------+
| 2.1 Verified Nutritional Ground Truth (Rule 1)   | 2.2 Hard Safety Gate (Rule 2)       |
| - 8,788 Foods (USDA FoodData Central)            | - Deterministic Pre-Filtering Gate  |
| - 528 Indian Foods (ICMR-NIN IFCT 2017)          | - Allergens (Nuts, Dairy, Gluten)   |
| - Zero LLM Hallucination of Nutritional Values   | - Medical / Lifestyle Constraints   |
+--------------------------------------------------+-------------------------------------+
                                            |
                                            v  [Safe Recipe Candidates & Nutrient Bounds]
+========================================================================================+
|                     LAYER 3: CORE ALGORITHMIC & HYBRID ML ENGINE                       |
+------------------------------+-------------------------------+-------------------------+
| 3.1 Metabolic Calculator     | 3.2 6-Factor Hybrid ML Scorer | 3.3 100% Macro Validator|
| - BMR = 10W + 6.25H - 5A ± s | - Score = Sum(w_i * s_i)      | - WHO Split:            |
| - TDEE = BMR * Activity      | - Macro (0.30), Goal (0.20),  |   * 50% Carbohydrates   |
| - Target = max(1200, TDEE-400)|   Pref (0.20), Feedback (0.15)|   * 20% Protein         |
|                              |   Diversity (0.10), Prep(0.05)|   * 30% Healthy Fats    |
+------------------------------+-------------------------------+-------------------------+
                                            |
                                            v  [Optimized Daily Meal Plan & SHAP Scores]
+========================================================================================+
|                      LAYER 4: HINGLISH EXECUTION & PRESENTATION                        |
+----------------------------------------------------------------------------------------+
| 4.1 Real-Time Pantry-to-Plate Matcher ("100% Samaan Available" vs "Missing Items")    |
| 4.2 Metric & Kitchen Measure Portion Guides (grams, tablespoons, cups)                 |
| 4.3 Step-by-Step Hinglish Cooking Guidance with Flame Levels & 1-Pan Cleanup Hacks     |
+----------------------------------------------------------------------------------------+
                                            |
                                            v  [Meal Eaten & User Feedback]
+========================================================================================+
|                       LAYER 5: ADAPTIVE CLOSED-LOOP FEEDBACK                           |
+----------------------------------------------------------------------------------------+
| 5.1 Post-Meal Ratings (1 to 5 Stars) & Liked/Disliked Aspects                          |
| 5.2 Ridge Regression Online Weight Adaptation (Updates preference_weights in DB)       |
+========================================================================================+
                                            |
                                            +--------------> (Feedback Loop back to Layer 3)
```

---

## Mathematical Formulations

### 1. Energy Expenditure & Caloric Target
$$\text{BMR} = 10 \cdot W + 6.25 \cdot H - 5 \cdot A + s \quad \text{where } s = \begin{cases} +5 & \text{Male} \\ -161 & \text{Female} \end{cases}$$

$$\text{TDEE} = \text{BMR} \times \alpha \quad (\alpha \in [1.2, 1.9])$$

$$\text{Target Calories} = \begin{cases} \max(1200, \text{TDEE} - 400) & \text{Cut (Fat Loss)} \\ \text{TDEE} & \text{Maintenance} \\ \text{TDEE} + 300 & \text{Lean Surplus} \end{cases}$$

### 2. Hybrid Recommendation Scoring Function
$$\text{Score}(r) = \sum_{i=1}^{6} w_i \cdot s_i(r)$$

$$\text{Score}(r) = 0.30\,s_{\text{macro}} + 0.20\,s_{\text{goal}} + 0.20\,s_{\text{pref}} + 0.15\,s_{\text{fb}} + 0.10\,s_{\text{div}} + 0.05\,s_{\text{prep}}$$

$$\text{subject to } \sum_{i=1}^{6} w_i = 1.0, \quad s_i(r) \in [0, 1] \; \forall i$$
