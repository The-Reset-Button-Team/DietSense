"""TF-IDF vectorization + cosine similarity between user and candidates."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def build_corpus_text(item: dict) -> str:
    """Flatten a food/recipe's text fields into one string for TF-IDF."""
    name = str(item.get("name") or "")
    tags = " ".join(str(t) for t in item.get("tags") or [])
    cuisine = str(item.get("cuisine") or "")
    return f"{name} {tags} {cuisine}".strip()


def build_user_text(user_profile: dict) -> str:
    """Same flattening, but from the user's stated preferences."""
    diet = str(user_profile.get("dietary_pref") or "")
    cuisines = " ".join(str(c) for c in user_profile.get("preferred_cuisines") or [])
    liked = " ".join(str(l) for l in user_profile.get("liked_tags") or [])
    return f"{diet} {cuisines} {liked}".strip()


def get_similarity(user_profile: dict, candidates: list[dict]) -> np.ndarray:
    """
    Returns a 1D array of cosine similarity scores, one per candidate,
    in the same order as `candidates`.
    Safely handles empty candidates list and empty vocabulary without crashing.
    """
    if not candidates:
        return np.zeros(0, dtype=float)

    corpus = [build_corpus_text(c) for c in candidates]
    user_text = build_user_text(user_profile)

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        # fit on candidates + user text together so vocab lines up
        all_vectors = vectorizer.fit_transform(corpus + [user_text])

        candidate_vectors = all_vectors[:-1]
        user_vector = all_vectors[-1]

        scores = cosine_similarity(user_vector, candidate_vectors)[0]
        return np.nan_to_num(scores, nan=0.0)
    except (ValueError, Exception):
        # Empty vocabulary (e.g. only stop words or symbols) -> return zeros safely
        return np.zeros(len(candidates), dtype=float)
