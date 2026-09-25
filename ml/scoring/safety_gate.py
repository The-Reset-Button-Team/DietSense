"""
DietSense - Hard Safety Gate (Rule Floor)
Runs strictly BEFORE ML scoring. Hard-excludes foods matching user's allergies
or dietary restrictions.
"""

from typing import List, Dict, Any


def filter_unsafe_foods(user_profile: Dict[str, Any], candidate_foods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter candidate foods by removing items containing any declared allergens
    or violating dietary restrictions.
    """
    # TODO: Implement hard allergen and diet exclusion logic
    pass
