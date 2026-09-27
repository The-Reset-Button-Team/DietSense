"""Standalone sanity check — run this BEFORE touching the API."""
from ml.recommendation.recommender import recommend

fake_user = {
    "dietary_pref": "vegetarian",
    "allergies": ["peanuts"],
    "budget_per_meal": 80,
    "prep_time_limit": 20,
    "target_calories": 1800,
    "preferred_cuisines": ["indian"],
    "liked_tags": ["light", "quick"],
}

fake_candidates = [
    {"name": "Vegetable Poha", "tags": ["veg", "light", "indian"], "allergens": [],
     "cuisine": "indian", "cost_estimate": 40, "prep_time": 15, "calories": 350},
    {"name": "Chicken Curry", "tags": ["non-veg", "indian"], "allergens": [],
     "cuisine": "indian", "cost_estimate": 120, "prep_time": 45, "calories": 500},
    {"name": "Peanut Noodles", "tags": ["veg", "asian"], "allergens": ["peanuts"],
     "cuisine": "asian", "cost_estimate": 60, "prep_time": 20, "calories": 450},
]

results = recommend(fake_user, fake_candidates, top_n=3)

for r in results:
    print(f"{r['item']['name']} | score={r['score']:.2f}")
    print(f" -> {r['reason']}")
