"""
bollywood_rerank.py - Simple reranking helper for Indian movie searches.

This module uses OMDb metadata to shift Indian or same-language movies
higher in the existing recommendation list without changing the ML model.
"""

from api.omdb import get_movie_details


def normalize_text(value):
    if not value:
        return ""
    return str(value).strip().lower()


def movie_score(movie, reference):
    score = 0

    movie_country = normalize_text(movie.get("country"))
    movie_language = normalize_text(movie.get("language"))
    movie_genre = normalize_text(movie.get("genre"))
    ref_country = normalize_text(reference.get("country"))
    ref_language = normalize_text(reference.get("language"))
    ref_genres = {genre.strip() for genre in normalize_text(reference.get("genre")).split(",") if genre.strip()}

    if "india" in movie_country:
        score += 12
    if ref_country and ref_country in movie_country:
        score += 8
    if ref_language and ref_language in movie_language:
        score += 10
    if movie_genre and ref_genres:
        overlap = sum(1 for genre in ref_genres if genre and genre in movie_genre)
        score += overlap * 4

    return score


def rerank_indian_recommendations(recommendations, reference_title):
    if not recommendations or not reference_title:
        return recommendations

    reference = get_movie_details(reference_title)

    if not reference.get("success"):
        return recommendations

    if "india" not in normalize_text(reference.get("country")):
        return recommendations

    enriched = []

    for movie in recommendations:
        details = get_movie_details(movie.get("title"), movie.get("year"))
        score_bonus = movie_score(details, reference)
        enriched.append((score_bonus, movie))

    enriched.sort(
        key=lambda item: (
            -item[0],
            -float(item[1].get("similarity_score", 0) or 0),
            item[1].get("title", ""),
        )
    )
    return [item[1] for item in enriched]
