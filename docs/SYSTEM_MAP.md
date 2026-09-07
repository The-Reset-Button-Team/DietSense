# DietSense — End-to-End System & User Journey Architecture Map

This document outlines the end-to-end system architecture, data flow, and user journey of **DietSense**.

Interactive Visual Studio: [`docs/system_map.html`](system_map.html)

---

## 🗺️ Visual System Architecture Map

```mermaid
flowchart TD
    subgraph STAGE1["1. User & Biometrics Profile"]
        A1["👤 User Inputs (Weight, Height, Age, Activity)"] --> A2["🔥 Mifflin-St Jeor Engine\nBMR & TDEE Target ± Goal Deficit"]
        A3["🍳 Solo Routine & Slot Customizer\n(2, 3, 4, 5 Meals / Custom)"] --> A4["⏱️ Weekday Effort Preferences\n(Low Effort BF <12m, Moderate Lunch)"]
    end

    subgraph STAGE2["2. AI Grocery & Pantry Engine"]
        B1["📸 Grocery Bill / Fridge Snapshot / Text"] --> B2["🤖 Multimodal Vision OCR Scanner"]
        B2 --> B3["🛒 Kitchen Stock Inventory Manager\n(Pulses, Dairy, Veggies, Spices)"]
        B3 --> B4["✨ Pantry-to-Plate Matcher\n(100% In-Stock vs Missing Items)"]
    end

    subgraph STAGE3["3. Authoritative Data & Safety Gate"]
        C1["📦 USDA FoodData Central & ICMR-NIN IFCT 2017"] --> C2["🗄️ PostgreSQL Database (11 Tables)"]
        C2 --> C3{"🛡️ Hard Safety Gate (Rule 2)\nAllergens / Vegan / Gluten / Medical"}
    end

    subgraph STAGE4["4. ML Recommendation & 100% Sync"]
        A2 & A4 & B4 & C3 --> D1["🧠 6-Factor Hybrid ML Scoring Engine\n(Macro, Goal, Pref, Feedback, Diversity, Prep)"]
        D1 --> D2["📊 SHAP Explainability Engine"]
        D2 --> D3["⚖️ Dynamic 100% Macro Validator\n(WHO Split: 50% Carbs, 20% Protein, 30% Fat)"]
    end

    subgraph STAGE5["5. Hinglish Cooking & Feedback"]
        D3 --> E1["🥣 Daily Meal Plan Display"]
        E1 --> E2["📖 Hinglish Step-by-Step Recipe Modal\n(1-Person Portions + Solo Hacks)"]
        E2 --> E3["⭐ Post-Meal Feedback & Rating (1-5)"]
        E3 --> E4["🔄 Adaptive Ridge Regression\n(Updates preference_weights vector)"]
    end

    E4 -.->|Continuous Learning| D1

    classDef stage1 fill:#eff6ff,stroke:#bfdbfe,stroke-width:1.5px,color:#1d4ed8;
    classDef stage2 fill:#ecfdf5,stroke:#a7f3d0,stroke-width:1.5px,color:#047857;
    classDef stage3 fill:#fdf2f4,stroke:#fbcfe8,stroke-width:1.5px,color:#581825;
    classDef stage4 fill:#f5f3ff,stroke:#ddd6fe,stroke-width:1.5px,color:#6d28d9;
    classDef stage5 fill:#fffbeb,stroke:#fde68a,stroke-width:1.5px,color:#b45309;

    class A1,A2,A3,A4 stage1;
    class B1,B2,B3,B4 stage2;
    class C1,C2,C3 stage3;
    class D1,D2,D3 stage4;
    class E1,E2,E3,E4 stage5;
```

---

## 5 Core System Layers

### 1. User & Biometrics Layer
- **Mifflin-St Jeor Formula**:
  - Men: `BMR = 10 × Weight(kg) + 6.25 × Height(cm) - 5 × Age + 5`
  - Women: `BMR = 10 × Weight(kg) + 6.25 × Height(cm) - 5 × Age - 161`
  - `TDEE = BMR × Activity Multiplier (1.2 to 1.9)`
  - Daily Target = `TDEE - 400 kcal` (Fat Loss Cut with 1200 kcal safety floor) or `TDEE + 300 kcal` (Lean Surplus).
- **Solo Cook Routine**: 1-person portion scaling with customizable meal slots (2-meal IF 16:8, 3-meal Classic, 4-meal Active, 5-meal Metabolic).

### 2. AI Grocery & Pantry Scanner (`Pantry-to-Plate`)
- **Multimodal OCR**: Detects food items from camera shots of fridge shelves, physical supermarket receipts, and digital delivery invoices (Blinkit/Zepto/Instamart).
- **Pantry Matching**: Ranks and flags recipes that can be cooked immediately using available stock (`✨ 100% Samaan Available`).

### 3. Safety Gate & Verified Data (Rule 1 & Rule 2)
- **Authoritative Data Sources**: 8,788 items from USDA FoodData Central + 528 items from ICMR-NIN (IFCT 2017).
- **Hard Safety Gate**: All dietary constraints and allergen flags are filtered out in SQL before scoring candidates.

### 4. 6-Factor Hybrid ML Scoring & Dynamic Validation
- **Scoring Equation**:
  $$\text{Score} = 0.30 \times \text{Macro} + 0.20 \times \text{Goal} + 0.20 \times \text{Pref} + 0.15 \times \text{Feedback} + 0.10 \times \text{Diversity} + 0.05 \times \text{Prep}$$
- **100% Dynamic Validation**: Target energy and macros are proportionally distributed across active meal slots and mathematically verified.

### 5. Hinglish Cooking & Adaptive Feedback
- **Hinglish Execution**: Step-by-step instructions with flame levels, metric/household measures, and solo kitchen cleanup hacks.
- **Adaptive Re-ranking**: Post-meal 1-5 ratings update the user's `preference_weights` vector in PostgreSQL.
