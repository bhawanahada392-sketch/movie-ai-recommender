"""
ranking_agent.py - Simple ranking agent.

This module combines similarity, IMDb rating, genre overlap, and intent match.
It does not change the recommendation model; it only sorts the candidate list.
"""


def parse_rating(value):
    """
    Convert IMDb rating text into a 0-to-1 number.

    Args:
        value: IMDb rating, often a string like "8.4".

    Returns:
        float: Rating score from 0 to 1.
    """
    try:
        return float(value) / 10
    except (TypeError, ValueError):
        return 0


def split_genres(genre_text):
    """
    Split OMDb genre text into lowercase genre words.

    Args:
        genre_text (str): Comma-separated genres from OMDb.

    Returns:
        set: Clean genre names.
    """
    if not genre_text or genre_text == "N/A":
        return set()

    return {genre.strip().lower() for genre in str(genre_text).split(",")}


def get_genre_overlap(movie, intent):
    """
    Score how well movie genres match the user's requested genres.

    Args:
        movie (dict): Enriched recommendation.
        intent (dict): Parsed user intent.

    Returns:
        float: 0 to 1 genre match score.
    """
    requested_genres = {genre.lower() for genre in intent.get("genre", [])}

    if not requested_genres:
        return 0

    movie_genres = split_genres(movie.get("genre"))

    if not movie_genres:
        return 0

    matches = requested_genres.intersection(movie_genres)
    return len(matches) / len(requested_genres)


def get_intent_match(movie, intent):
    """
    Score simple keyword matches in title, genre, and plot.

    Args:
        movie (dict): Enriched recommendation.
        intent (dict): Parsed user intent.

    Returns:
        float: 0 to 1 intent match score.
    """
    keywords = intent.get("keywords", [])

    if not keywords:
        return 0

    searchable_text = " ".join(
        [
            str(movie.get("title", "")),
            str(movie.get("genre", "")),
            str(movie.get("plot", "")),
        ]
    ).lower()

    match_count = 0

    for keyword in keywords:
        if keyword.lower() in searchable_text:
            match_count += 1

    return match_count / len(keywords)


def parse_runtime_minutes(runtime_text):
    """
    Convert runtime text like '117 min' into minutes.

    Args:
        runtime_text (str): Runtime from OMDb.

    Returns:
        int: Runtime minutes, or 0 if unavailable.
    """
    if not runtime_text or runtime_text == "N/A":
        return 0

    digits = "".join(
        character for character in str(runtime_text) if character.isdigit()
    )

    if not digits:
        return 0

    return int(digits)


def get_runtime_match(movie, intent):
    """
    Score whether the movie fits runtime preferences.

    Args:
        movie (dict): Enriched recommendation.
        intent (dict): Parsed user intent.

    Returns:
        float: 0 to 1 runtime match score.
    """
    runtime_preferences = intent.get("runtime_preference", [])

    if "under_2_hours" not in runtime_preferences:
        return 0

    minutes = parse_runtime_minutes(movie.get("runtime"))

    if minutes and minutes <= 120:
        return 1

    return 0


def calculate_rank_score(movie, intent):
    """
    Combine simple ranking signals into one score.

    Args:
        movie (dict): Enriched recommendation.
        intent (dict): Parsed user intent.

    Returns:
        float: Combined ranking score.
    """
    similarity = float(movie.get("similarity_score", 0) or 0)
    rating = parse_rating(movie.get("rating"))
    genre_overlap = get_genre_overlap(movie, intent)
    intent_match = get_intent_match(movie, intent)
    runtime_match = get_runtime_match(movie, intent)
    poster_score = 1 if movie.get("poster") and movie.get("poster") != "N/A" else 0

    return (
        similarity * 0.42
        + rating * 0.18
        + genre_overlap * 0.20
        + intent_match * 0.10
        + runtime_match * 0.05
        + poster_score * 0.05
    )


def rank_recommendations(recommendations, intent):
    """
    Sort recommendations using simple combined ranking.

    Args:
        recommendations (list): Enriched recommendation dictionaries.
        intent (dict): Parsed user intent.

    Returns:
        list: Sorted recommendations. Existing fields are preserved.
    """
    indexed_movies = list(enumerate(recommendations))

    indexed_movies.sort(
        key=lambda item: (
            -calculate_rank_score(item[1], intent),
            item[0],
        )
    )

    return [movie for index, movie in indexed_movies]
