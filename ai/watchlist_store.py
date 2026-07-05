"""
watchlist_store.py - Tiny in-memory watchlist helper.

There is no database and no login. The frontend can store IDs in Local Storage,
while these endpoints can accept and return movie dictionaries when needed.
"""

WATCHLIST_ITEMS = []


def get_movie_key(movie):
    """
    Build a simple key for a movie dictionary.

    Args:
        movie (dict): Movie data from the frontend.

    Returns:
        str: Movie id or title key.
    """
    if not isinstance(movie, dict):
        return str(movie or "").lower()

    return str(movie.get("id") or movie.get("title") or "").lower()


def add_to_watchlist(movie):
    """
    Add one movie to the in-memory watchlist.

    Args:
        movie (dict): Movie data to store.

    Returns:
        list: Updated watchlist.
    """
    movie_key = get_movie_key(movie)

    if not movie_key:
        return WATCHLIST_ITEMS

    for existing_movie in WATCHLIST_ITEMS:
        if get_movie_key(existing_movie) == movie_key:
            return WATCHLIST_ITEMS

    WATCHLIST_ITEMS.append(movie)
    return WATCHLIST_ITEMS


def remove_from_watchlist(movie):
    """
    Remove one movie from the in-memory watchlist.

    Args:
        movie (dict): Movie id or title to remove.

    Returns:
        list: Updated watchlist.
    """
    movie_key = get_movie_key(movie)

    if not movie_key:
        return WATCHLIST_ITEMS

    WATCHLIST_ITEMS[:] = [
        existing_movie
        for existing_movie in WATCHLIST_ITEMS
        if get_movie_key(existing_movie) != movie_key
    ]

    return WATCHLIST_ITEMS


def get_watchlist():
    """
    Return all watchlist movies.

    Returns:
        list: Watchlist items.
    """
    return WATCHLIST_ITEMS


def clear_watchlist():
    """
    Remove all watchlist movies.

    Returns:
        list: Empty watchlist.
    """
    WATCHLIST_ITEMS.clear()
    return WATCHLIST_ITEMS
