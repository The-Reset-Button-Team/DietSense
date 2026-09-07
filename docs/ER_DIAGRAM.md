# DietSense - Classical Entity-Relationship (ER) Model

## 1. Classical Peter Chen Notation (Rectangles, Diamonds & Cardinalities)

In classical database design:
* **[ RECTANGLE ]** = **Entity** (Table)
* **< DIAMOND >** = **Relationship** (Link / Association)
* **( OVAL )** = **Attribute** (_underline_ denotes Primary Key PK)
* **1 : 1, 1 : N, N : 1** = **Cardinality Constraints**

`
                       ( daily_tdee )
                             |
 ( email ) ---- [ USERS ] ---- ( _id_ )
                  |   |   |
     +------------+   |   +--------------------------+
     |                |                              |
    1|               1|                             1|
     v                v                              v
< HAS_LIMITS >   < STOCKS >                    < GENERATES >
     |                |                              |
    1|               N|                             N|
     v                v                              v
[ DIETARY_     [ PANTRY_ITEMS ]                [ MEAL_PLANS ]
RESTRICTIONS ]        |                              |
                      |                             1|
                      |                              v
                      |                         < CONTAINS >
                      |                              |
                      |                             N|
                      |                              v
                      |                    [ MEAL_PLAN_ITEMS ]
                      |                              |
                      |                             N|
                      |                              v
                      |                         < SUGGESTS >
                      |                              |
                      |                             1|
                      |                              v
                      +-----------------------> [ RECIPES ] ---- ( prep_time )
                                                     |    \
                                                     |     \---- ( _id_ )
                                                    1|
                                                     v
                                                < AUDITS >
                                                     |
                                                    N|
                                                     v
                                             [ AI_SAFETY_AUDITS ]
`

---

## 2. Cardinality & Constraint Breakdown

| Relationship | Entity 1 | Cardinality | Entity 2 | Meaning / Rule |
| :--- | :--- | :---: | :--- | :--- |
| **HAS_LIMITS** | USERS | **1 : 1** | DIETARY_RESTRICTIONS | Har user profile ka exactly 1 safety gate barrier (allergens, veg/halal flags). |
| **STOCKS** | USERS | **1 : N** | PANTRY_ITEMS | User apne fridge/kitchen me multiple grocery ingredients scan karke rakh sakta hai. |
| **GENERATES** | USERS | **1 : N** | MEAL_PLANS | User din-ba-din multiple meal plans calculate aur execute kar sakta hai. |
| **CONTAINS** | MEAL_PLANS | **1 : N** | MEAL_PLAN_ITEMS | 1 Meal plan ke andar customizable active slots (e.g. 2, 3, ya 4 meals) hote hain. |
| **SUGGESTS** | MEAL_PLAN_ITEMS | **N : 1** | RECIPES | Har meal slot verified ICMR-NIN / USDA catalog recipe ko reference karta hai. |
| **AUDITS** | RECIPES | **1 : N** | AI_SAFETY_AUDITS | Har recipe scoring/generation ka safety audit log maintain hota hai. |

---

## 3. Entity Definitions & Schema

* **USERS** (id PK, email, ge, gender, height_cm, weight_kg, goal, ctivity_level, daily_calorie_target)
* **DIETARY_RESTRICTIONS** (id PK, user_id FK, is_veg, is_vegan, llergen_flags[], medical_conditions[])
* **PANTRY_ITEMS** (id PK, user_id FK, item_name, quantity, unit, is_in_stock)
* **MEAL_PLANS** (id PK, user_id FK, plan_date, status, 	otal_calories, 	otal_protein_g)
* **MEAL_PLAN_ITEMS** (id PK, meal_plan_id FK, slot_name, ecipe_id FK, 	arget_calories, 	arget_protein_g)
* **RECIPES** (id PK, 	itle, calories, protein_g, prep_time_mins, instructions_hinglish, solo_hacks)
* **AI_SAFETY_AUDITS** (id PK, user_id FK, ecipe_id FK, passed_safety, ilter_reason, 	imestamp)

---

## 4. Visual Files

* **Classical HTML Interactive Diagram**: [er_diagram_classical.html](file:///c:/Users/impro/Dev/DietSense-/docs/er_diagram_classical.html)
* **Tabular Relational Schema Explorer**: [er_diagram.html](file:///c:/Users/impro/Dev/DietSense-/docs/er_diagram.html)
