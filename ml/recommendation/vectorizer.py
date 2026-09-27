"""TF-IDF vectorization + cosine similarity between user and candidates."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def build_corpus_text(item: dict) -> str:
    """Flatten a food/recipe's text fields into one string for TF-IDF."""
    return " ".join([
        item.get("name", ""),
        " ".join(item.get("tags", [])),
        item.get("cuisine", ""),
    ])

def build_user_text(user_profile: dict) -> str:
    """Same flattening, but from the user's stated preferences."""
    return " ".join([
        user_profile.get("dietary_pref", ""),
        " ".join(user_profile.get("preferred_cuisines", [])),
        " ".join(user_profile.get("liked_tags", [])),
    ])

def get_similarity(user_profile: dict, candidates: list[dict]) -> np.ndarray:
    """
    Returns a 1D array of cosine similarity scores, one per candidate,
    in the same order as `candidates`.
    """
    corpus = [build_corpus_text(c) for c in candidates]
    user_text = build_user_text(user_profile)

    vectorizer = TfidfVectorizer(stop_words="english")
    # fit on candidates + user text together so vocab lines up
    all_vectors = vectorizer.fit_transform(corpus + [user_text])
    
    candidate_vectors = all_vectors[:-1]
    user_vector = all_vectors[-1]
    
    scores = cosine_similarity(user_vector, candidate_vectors)[0]
    return scores
