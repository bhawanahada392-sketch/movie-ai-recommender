"""
recent_searches.py - Lightweight recent-search helper.

This is intentionally small. It supports Local Storage style integration
without authentication or a database.
"""

RECENT_SEARCHES = []
MAX_RECENT_SEARCHES = 10


def add_recent_search(query):
    """
    Add a query to recent searches.

    Args:
        query (str): Search text.

    Returns:
        list: Updated recent searches.
    """
    clean_query = str(query or "").strip()

    if not clean_query:
        return RECENT_SEARCHES

    if clean_query in RECENT_SEARCHES:
        RECENT_SEARCHES.remove(clean_query)

    RECENT_SEARCHES.insert(0, clean_query)
    del RECENT_SEARCHES[MAX_RECENT_SEARCHES:]

    return RECENT_SEARCHES


def get_recent_searches():
    """
    Return saved recent searches.

    Returns:
        list: Recent search strings.
    """
    return RECENT_SEARCHES


def clear_recent_searches():
    """
    Clear all recent searches.

    Returns:
        list: Empty recent-search list.
    """
    RECENT_SEARCHES.clear()
    return RECENT_SEARCHES
