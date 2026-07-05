"""
recommendation_agent.py - Simple recommendation agent.

This module keeps the existing ML recommender for known movie titles.
For natural-language searches, it uses keywords against the existing dataset.
"""

from difflib import get_close_matches

from ml.recommender import format_year, movies_df, recommend_movies


FALLBACK_KEYWORDS = {
    "friends": ["friendship", "comedy", "adventure"],
    "weekend": ["adventure", "action", "comedy"],
    "binge": ["adventure", "series", "epic"],
    "rainy evening": ["drama", "romance", "mystery"],
    "date night": ["romance", "comedy"],
    "feel good": ["comedy", "family", "friendship"],
    "funny": ["comedy"],
    "emotional": ["drama"],
    "mind bending": ["mystery", "thriller", "dream"],
    "under_2_hours": ["comedy", "family", "animation"],
}


def get_all_titles():
    """
    Read all movie titles from the existing dataset.

    Returns:
        list: Movie titles.
    """
    if movies_df is None:
        return []

    return [str(title) for title in movies_df["title"].tolist()]


def find_fuzzy_title(user_title):
    """
    Find the closest dataset title for a misspelled title.

    Args:
        user_title (str): Title typed by the user.

    Returns:
        str: Closest title, or an empty string.
    """
    if not user_title:
        return ""

    titles = get_all_titles()
    lower_to_title = {title.lower(): title for title in titles}
    matches = get_close_matches(
        user_title.lower(),
        list(lower_to_title.keys()),
        n=1,
        cutoff=0.72,
    )

    if not matches:
        return ""

    return lower_to_title[matches[0]]


def run_title_recommendation(movie_title):
    """
    Use the existing ML recommender for a movie title.

    Args:
        movie_title (str): Known or fuzzy-matched movie title.

    Returns:
        dict: Existing recommender result.
    """
    return recommend_movies(movie_title)


def score_dataset_row(row, intent):
    """
    Give one dataset row a simple keyword score.

    Args:
        row: A pandas row from the processed dataset.
        intent (dict): Parsed intent from intent_agent.

    Returns:
        int: Higher means a better natural-language match.
    """
    combined_features = str(row.get("combined_features", "")).lower()
    title = str(row.get("title", "")).lower()
    score = 0

    for genre in intent.get("genre", []):
        if genre in combined_features:
            score += 4

    expanded_keywords = list(intent.get("keywords", []))

    for label in intent.get("mood", []):
        expanded_keywords.extend(FALLBACK_KEYWORDS.get(label, []))

    for label in intent.get("occasion", []):
        expanded_keywords.extend(FALLBACK_KEYWORDS.get(label, []))

    for label in intent.get("runtime_preference", []):
        expanded_keywords.extend(FALLBACK_KEYWORDS.get(label, []))

    for mood in intent.get("mood", []):
        if mood in combined_features or mood in title:
            score += 3

    for occasion in intent.get("occasion", []):
        if occasion in combined_features or occasion in title:
            score += 2

    for keyword in expanded_keywords:
        if keyword in combined_features:
            score += 2
        if keyword in title:
            score += 3

    return score


def search_dataset_by_intent(intent, limit=20):
    """
    Recommend movies from dataset keywords when no title is found.

    Args:
        intent (dict): Parsed natural-language intent.
        limit (int): How many candidates to return before final ranking.

    Returns:
        dict: Recommendation-style result.
    """
    if movies_df is None:
        return {
            "success": False,
            "message": "Resources not loaded.",
            "recommendations": [],
        }

    scored_movies = []

    for index, row in movies_df.iterrows():
        score = score_dataset_row(row, intent)

        if score > 0:
            scored_movies.append((score, index, row))

    scored_movies.sort(key=lambda item: (-item[0], item[1]))

    recommendations = []

    for score, index, row in scored_movies[:limit]:
        recommendations.append(
            {
                "id": int(row["id"]),
                "title": row["title"],
                "year": format_year(row.get("year", "")),
                "similarity_score": round(min(score / 20, 0.99), 2),
            }
        )

    if not recommendations:
        return {
            "success": False,
            "message": "Movie not found.",
            "recommendations": [],
        }

    return {
        "success": True,
        "movie": intent.get("raw_query", "your search"),
        "recommendations": recommendations,
    }


def get_recommendations_for_intent(intent):
    """
    Choose title-based or natural-language recommendation flow.

    Args:
        intent (dict): Parsed user intent.

    Returns:
        dict: Recommendation result plus the resolved title.
    """
    exact_title = intent.get("exact_movie_title", "")

    if exact_title:
        result = run_title_recommendation(exact_title)
        result["resolved_title"] = exact_title
        return result

    fuzzy_title = find_fuzzy_title(intent.get("movie_title", ""))

    if fuzzy_title:
        result = run_title_recommendation(fuzzy_title)
        result["resolved_title"] = fuzzy_title
        result["fuzzy_match"] = True
        return result

    result = search_dataset_by_intent(intent)
    result["resolved_title"] = ""
    return result
