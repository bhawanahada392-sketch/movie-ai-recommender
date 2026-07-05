"""
explanation_agent.py - Explanation agent helpers.

This module keeps the existing Gemini overview explanation and adds a simple
one-sentence reason for each recommended movie.
"""

from ai.ai_explainer import generate_movie_explanation


def build_movie_reason(searched_movie, movie, intent):
    """
    Create a one-sentence reason for one movie.

    Args:
        searched_movie (str): User search text or resolved movie title.
        movie (dict): One enriched recommendation.
        intent (dict): Parsed user intent.

    Returns:
        str: Friendly one-sentence reason.
    """
    genres = movie.get("genre", "similar themes")

    if intent.get("genre"):
        return (
            f"Recommended because it matches your interest in "
            f"{', '.join(intent['genre'])} stories while offering a {genres} mood."
        )

    if intent.get("mood"):
        return (
            f"Recommended because it fits the {', '.join(intent['mood'])} feeling "
            f"you asked for."
        )

    return (
        f"Recommended because it shares {searched_movie}'s sense of story, "
        f"tone, or cinematic atmosphere."
    )


def add_individual_reasons(searched_movie, recommendations, intent):
    """
    Add one recommendation reason to each movie dictionary.

    Args:
        searched_movie (str): User search text or resolved title.
        recommendations (list): Enriched recommendation dictionaries.
        intent (dict): Parsed user intent.

    Returns:
        list: Same recommendations with recommendation_reason added.
    """
    for movie in recommendations:
        movie["recommendation_reason"] = build_movie_reason(
            searched_movie,
            movie,
            intent,
        )

    return recommendations


def generate_overview_explanation(searched_movie, recommendations):
    """
    Use the existing Gemini helper for the overview explanation.

    Args:
        searched_movie (str): User search text or resolved title.
        recommendations (list): Final recommendation list.

    Returns:
        str: Gemini explanation, or an empty string on failure.
    """
    return generate_movie_explanation(searched_movie, recommendations)
