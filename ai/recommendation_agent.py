"""
recommendation_agent.py - Simple recommendation agent.

This module keeps the existing ML recommender for known movie titles.
It also supports exact actor, director, and genre searches using the
metadata saved in processed_movies.csv.
"""

import re
from difflib import get_close_matches

from ml.recommender import format_year, movies_df, recommend_movies

TITLE_ALIASES = {
    "bahubali": "Baahubali: The Beginning",
    "bahubali the beginning": "Baahubali: The Beginning",
    "bahubali 2": "Baahubali 2: The Conclusion",
    "kgf": "K.G.F: Chapter 1",
    "kgf chapter 1": "K.G.F: Chapter 1",
    "kgf chapter 2": "K.G.F: Chapter 2",
}


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


def normalize_query(value):
    """
    Normalize user text for reliable matching.

    Args:
        value: Raw text.

    Returns:
        str: Lowercase text with simple spacing.
    """
    text = str(value or "").lower().strip()
    text = text.replace("sci-fi", "science fiction")
    text = text.replace("scifi", "science fiction")
    text = re.sub(r"[^a-z0-9&.:\-'\s]", " ", text)
    return " ".join(text.split())


def normalize_metadata_phrase(value):
    """
    Normalize cast/director/genre text for matching names inside a field.
    """
    text = str(value or "").lower()
    text = text.replace("sci-fi", "science fiction")
    text = text.replace("scifi", "science fiction")
    text = re.sub(r"[\[\]{}\"|,/;:]+", " ", text)
    text = re.sub(r"[^a-z0-9&'\s-]", " ", text)
    return " ".join(text.split())


def compact_text(value):
    """
    Remove punctuation and spaces for title comparisons like K.G.F vs KGF.
    """
    return re.sub(r"[^a-z0-9]", "", normalize_query(value))


def compact_tokens(value):
    """
    Return punctuation-free tokens for safe short-title matching.
    """
    tokens = normalize_query(value).split()
    return [re.sub(r"[^a-z0-9]", "", token) for token in tokens if token]


def dataframe_has_column(column_name):
    return movies_df is not None and column_name in movies_df.columns


def clean_field(value):
    """Return a safe string for values coming from pandas rows."""
    if value is None:
        return ""

    text = str(value).strip()
    if text.lower() in {"nan", "none", "n/a"}:
        return ""

    return text


def contains_exact_phrase(value, query):
    """
    Match a full name or genre phrase without matching longer names.

    Example: "tom holland" should not match "tom hollander".
    """
    if not query:
        return False

    text = normalize_metadata_phrase(value)
    clean_query = normalize_metadata_phrase(query)
    escaped_query = re.escape(clean_query)
    return re.search(rf"(^|\s){escaped_query}($|\s)", text) is not None


def row_to_recommendation(row, score):
    """
    Convert a dataset row into the response shape used by the app.
    """
    return {
        "id": int(row["id"]),
        "title": row["title"],
        "year": format_year(row.get("year", "")),
        "similarity_score": round(float(score), 2),
        "genre": clean_field(row.get("genres", "")),
        "genres": clean_field(row.get("genres", "")),
        "plot": clean_field(row.get("overview", "")),
        "overview": clean_field(row.get("overview", "")),
        "cast": clean_field(row.get("cast", "")),
        "director": clean_field(row.get("director", "")),
        "language": clean_field(row.get("language", "")),
        "poster": clean_field(row.get("poster", "")),
        "rating": clean_field(row.get("rating", "")),
    }


def sort_metadata_matches(dataframe, limit):
    """
    Sort exact metadata matches by rating and metadata richness.
    """
    rows = []

    for index, row in dataframe.iterrows():
        try:
            rating = float(row.get("rating", 0) or 0)
        except (TypeError, ValueError):
            rating = 0

        richness = 0
        for column in ["overview", "genres", "cast", "director", "keywords"]:
            if str(row.get(column, "")).strip():
                richness += 1

        rows.append((rating, richness, index, row))

    rows.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return [row_to_recommendation(row, min(0.99, 0.70 + rating / 40)) for rating, richness, index, row in rows[:limit]]


def find_exact_title(user_title):
    """
    Find an exact title using normal and punctuation-insensitive matching.
    """
    if not user_title or movies_df is None:
        return ""

    query = normalize_query(user_title)
    compact_query = compact_text(user_title)
    alias = TITLE_ALIASES.get(query) or TITLE_ALIASES.get(compact_query)

    if alias:
        return alias

    for title in get_all_titles():
        if normalize_query(title) == query or compact_text(title) == compact_query:
            return title

    return ""


def find_partial_title(user_title):
    """
    Find the best partial title match after exact metadata checks.
    """
    if not user_title or movies_df is None:
        return ""

    query = normalize_query(user_title)
    compact_query = compact_text(user_title)
    candidates = []

    for title in get_all_titles():
        title_text = normalize_query(title)
        compact_title = compact_text(title)
        title_tokens = compact_tokens(title)

        if len(compact_query) <= 3:
            is_match = compact_query in title_tokens
        else:
            is_match = query in title_text or compact_query in compact_title

        if is_match:
            candidates.append((len(title_text), title))

    if not candidates:
        return ""

    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


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
    lower_to_title = {normalize_query(title): title for title in titles}
    matches = get_close_matches(
        normalize_query(user_title),
        list(lower_to_title.keys()),
        n=1,
        cutoff=0.78,
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


def search_exact_actor(actor_name, limit=20):
    """
    Return movies where the cast contains the exact actor phrase.
    """
    if not dataframe_has_column("cast"):
        return []

    query = normalize_query(actor_name)
    if not query:
        return []

    matches = movies_df[
        movies_df["cast"].fillna("").apply(
            lambda value: contains_exact_phrase(value, query)
        )
    ]
    return sort_metadata_matches(matches, limit)


def search_exact_director(director_name, limit=20):
    """
    Return movies where the director matches the exact director phrase.
    """
    if not dataframe_has_column("director"):
        return []

    query = normalize_query(director_name)
    if not query:
        return []

    matches = movies_df[
        movies_df["director"].fillna("").apply(
            lambda value: contains_exact_phrase(value, query)
        )
    ]
    return sort_metadata_matches(matches, limit)


def search_exact_genre(genre_name, limit=20):
    """
    Return movies that match an exact genre phrase.
    """
    if not dataframe_has_column("genres"):
        return []

    query = normalize_query(genre_name)
    if not query:
        return []

    matches = movies_df[
        movies_df["genres"].fillna("").apply(
            lambda value: contains_exact_phrase(value, query)
        )
    ]
    return sort_metadata_matches(matches, limit)


def detect_query_type(search_text):
    """
    Detect whether a query is a movie, actor, director, genre, or unknown.
    """
    exact_title = find_exact_title(search_text)
    if exact_title:
        return "movie", exact_title

    actor_matches = search_exact_actor(search_text, limit=1)
    if actor_matches:
        return "actor", search_text

    director_matches = search_exact_director(search_text, limit=1)
    if director_matches:
        return "director", search_text

    genre_matches = search_exact_genre(search_text, limit=1)
    if genre_matches:
        return "genre", search_text

    return "unknown", ""


def metadata_search_result(search_text, query_type=None):
    """
    Apply exact actor, director, then genre search priority.
    """
    search_functions = [
        ("actor", search_exact_actor),
        ("director", search_exact_director),
        ("genre", search_exact_genre),
    ]

    for label, search_function in search_functions:
        if query_type and label != query_type:
            continue

        recommendations = search_function(search_text)

        if recommendations:
            return {
                "success": True,
                "movie": search_text,
                "resolved_title": search_text,
                "match_type": label,
                "recommendations": recommendations,
            }

    return None


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
                "genre": clean_field(row.get("genres", "")),
                "genres": clean_field(row.get("genres", "")),
                "plot": clean_field(row.get("overview", "")),
                "overview": clean_field(row.get("overview", "")),
                "cast": clean_field(row.get("cast", "")),
                "director": clean_field(row.get("director", "")),
                "language": clean_field(row.get("language", "")),
                "poster": clean_field(row.get("poster", "")),
                "rating": clean_field(row.get("rating", "")),
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
    raw_query = intent.get("raw_query", "")
    possible_title = intent.get("movie_title", "")
    query_type, detected_value = detect_query_type(raw_query)
    exact_title = intent.get("exact_movie_title", "") or find_exact_title(possible_title)

    if query_type == "movie":
        exact_title = detected_value

    if exact_title:
        result = run_title_recommendation(exact_title)
        result["resolved_title"] = exact_title
        result["match_type"] = "exact_title"
        return result

    if query_type in {"actor", "director", "genre"}:
        metadata_result = metadata_search_result(raw_query, query_type)
        if metadata_result:
            return metadata_result

    metadata_result = metadata_search_result(raw_query)
    if metadata_result:
        return metadata_result

    partial_title = find_partial_title(possible_title or raw_query)
    if partial_title:
        result = run_title_recommendation(partial_title)
        result["resolved_title"] = partial_title
        result["match_type"] = "partial_title"
        return result

    fuzzy_title = find_fuzzy_title(possible_title or raw_query)

    if fuzzy_title:
        result = run_title_recommendation(fuzzy_title)
        result["resolved_title"] = fuzzy_title
        result["fuzzy_match"] = True
        result["match_type"] = "fuzzy_title"
        return result

    result = search_dataset_by_intent(intent)
    result["resolved_title"] = ""
    return result
