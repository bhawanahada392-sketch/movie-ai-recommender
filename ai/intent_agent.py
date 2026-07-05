"""
intent_agent.py - Simple keyword-based intent detection.

This file does not use an LLM. It looks for beginner-friendly keywords
inside the user's search text and turns them into a small intent dictionary.
"""

import re

from ml.recommender import movies_df


GENRE_KEYWORDS = {
    "action": ["action", "fight", "explosive", "adventure"],
    "adventure": ["adventure", "journey", "quest"],
    "animation": ["animated", "animation", "cartoon"],
    "comedy": ["funny", "comedy", "laugh", "hilarious"],
    "drama": ["drama", "emotional", "moving", "serious"],
    "family": ["family", "kids", "children", "child"],
    "fantasy": ["fantasy", "magic", "dragon", "dragons"],
    "horror": ["horror", "scary", "creepy", "ghost"],
    "romance": ["romantic", "romance", "date night", "love"],
    "science fiction": ["sci-fi", "scifi", "science fiction", "space", "alien", "aliens"],
    "thriller": ["thriller", "suspense", "mystery", "tense"],
}

MOOD_KEYWORDS = {
    "feel good": ["feel good", "comfort", "happy", "uplifting"],
    "funny": ["funny", "laugh", "comedy", "hilarious"],
    "emotional": ["emotional", "sad", "moving", "heartfelt"],
    "mind bending": ["mind bending", "confusing", "twist", "thought provoking"],
    "scary": ["scary", "creepy", "horror"],
}

OCCASION_KEYWORDS = {
    "family": ["family", "kids", "children"],
    "friends": ["friends", "group"],
    "date night": ["date night", "romantic"],
    "weekend": ["weekend", "binge"],
    "rainy evening": ["rainy", "cozy evening"],
    "girls night": ["girls night"],
}

RUNTIME_KEYWORDS = {
    "under_2_hours": ["under 2 hours", "less than 2 hours", "short movie", "quick movie"],
    "binge": ["binge", "weekend"],
}

STOP_PHRASES = [
    "movies like",
    "movie like",
    "films like",
    "film like",
    "movie for",
    "movies for",
    "something",
]


def normalize_text(text):
    """
    Make user text easier to compare.

    Args:
        text (str): Raw text typed by the user.

    Returns:
        str: Lowercase text with simple spacing.
    """
    return " ".join(str(text or "").lower().strip().split())


def find_matches(text, keyword_map):
    """
    Find labels whose keyword list appears in the text.

    Args:
        text (str): Normalized user text.
        keyword_map (dict): Labels mapped to example words.

    Returns:
        list: Labels that matched the text.
    """
    matches = []

    for label, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in text:
                matches.append(label)
                break

    return matches


def extract_possible_title(original_text):
    """
    Guess a movie title from phrases like 'movies like Avatar'.

    Args:
        original_text (str): Raw user text.

    Returns:
        str: Possible movie title, or an empty string.
    """
    clean_input = str(original_text or "").strip()
    lower_input = clean_input.lower()

    for phrase in STOP_PHRASES:
        if lower_input.startswith(phrase + " "):
            return clean_input[len(phrase):].strip(" .!?")

    # If the query has only a few words and no intent words, it may be a title.
    words = clean_input.split()
    has_intent = (
        find_matches(lower_input, GENRE_KEYWORDS)
        or find_matches(lower_input, MOOD_KEYWORDS)
        or find_matches(lower_input, OCCASION_KEYWORDS)
    )

    if words and len(words) <= 4 and not has_intent:
        return clean_input.strip(" .!?")

    return ""


def extract_keywords(text):
    """
    Pull useful search words from natural-language text.

    Args:
        text (str): Normalized user text.

    Returns:
        list: Simple keywords for dataset filtering.
    """
    words = re.findall(r"[a-z0-9]+", text)
    ignored_words = {
        "movie",
        "movies",
        "film",
        "films",
        "for",
        "with",
        "like",
        "want",
        "something",
        "the",
        "and",
        "under",
        "hours",
    }

    return [word for word in words if word not in ignored_words]


def find_exact_title(possible_title):
    """
    Check whether the possible title exists in the dataset.

    Args:
        possible_title (str): Movie title guessed from the query.

    Returns:
        str: Dataset title with correct capitalization, or empty string.
    """
    if not possible_title or movies_df is None:
        return ""

    clean_title = possible_title.strip().lower()
    matches = movies_df[movies_df["title"].str.lower() == clean_title]

    if len(matches) == 0:
        return ""

    return str(matches.iloc[0]["title"])


def extract_intent(user_query):
    """
    Convert a search query into simple intent fields.

    Args:
        user_query (str): Movie title or natural-language request.

    Returns:
        dict: Extracted genre, mood, occasion, runtime, keywords, and title.
    """
    normalized_query = normalize_text(user_query)
    possible_title = extract_possible_title(user_query)
    exact_title = find_exact_title(possible_title)

    return {
        "raw_query": str(user_query or "").strip(),
        "genre": find_matches(normalized_query, GENRE_KEYWORDS),
        "mood": find_matches(normalized_query, MOOD_KEYWORDS),
        "occasion": find_matches(normalized_query, OCCASION_KEYWORDS),
        "runtime_preference": find_matches(normalized_query, RUNTIME_KEYWORDS),
        "keywords": extract_keywords(normalized_query),
        "movie_title": exact_title or possible_title,
        "exact_movie_title": exact_title,
    }
