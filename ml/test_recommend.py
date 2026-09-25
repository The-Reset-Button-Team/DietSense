"""
DietSense - Standalone Recommendation Test Runner
Runs the Phase 3 deliverable: recommend(user_profile) -> ranked list with explanation strings.
Tests the ML pipeline independently of FastAPI and Supabase.
"""

from ml.scoring.safety_gate import filter_unsafe_foods
from ml.recommendation.recommender import recommend


def run_standalone_test():
    """
    Executes an end-to-end recommendation run on mock user profile and candidate meals.
    """
    mock_user_profile = {
        "user_id": "usr_test_1",
        "diet": "vegetarian",
        "budget": 200,
        "prep_time_limit": 20,
        "allergies": ["peanut"],
    }

    mock_candidates = [
        {
            "id": 1,
            "name": "Moong Dal Khichdi",
            "allergens": [],
            "is_vegetarian": True,
            "prep_time": 15,
            "cost": 60,
        },
        {
            "id": 2,
            "name": "Peanut Butter Oats",
            "allergens": ["peanut"],
            "is_vegetarian": True,
            "prep_time": 5,
            "cost": 40,
        },
    ]

    print("Running standalone recommendation test...")
    # TODO: Verify safety gate excludes peanut dish and scores are generated
    pass


if __name__ == "__main__":
    run_standalone_test()
