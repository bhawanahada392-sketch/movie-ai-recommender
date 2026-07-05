"""
dynamic_cache.py - Local JSON cache for movies outside the dataset.

This cache never edits the original CSV dataset. It only stores metadata
fetched through the existing OMDb helper for future use.
"""

import json
import os

from api.omdb import get_movie_details

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "data", "dynamic_movie_cache.json")


def load_dynamic_cache():
    """
    Load cached dynamic movie metadata from JSON.

    Returns:
        dict: Cached movie metadata keyed by lowercase title.
    """
    if not os.path.exists(CACHE_FILE):
        return {}

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def save_dynamic_cache(cache_data):
    """
    Save dynamic movie metadata to JSON.

    Args:
        cache_data (dict): Metadata to save.
    """
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(cache_data, file, indent=2)
    except OSError:
        print("Dynamic movie cache could not be saved.")


def get_or_fetch_dynamic_movie(title):
    """
    Fetch and cache metadata for a movie not found in the dataset.

    Args:
        title (str): Movie title to fetch.

    Returns:
        dict: Cached or fetched metadata.
    """
    clean_title = str(title or "").strip()

    if not clean_title:
        return {}

    cache_key = clean_title.lower()
    cache_data = load_dynamic_cache()

    if cache_key in cache_data:
        return cache_data[cache_key]

    omdb_data = get_movie_details(clean_title)

    if omdb_data.get("success"):
        cache_data[cache_key] = omdb_data
        save_dynamic_cache(cache_data)
        return omdb_data

    return {}
