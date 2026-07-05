"""
omdb.py - OMDb API helper functions.

This module fetches movie details (poster, rating, plot, etc.)
from the OMDb API. The ML model still chooses recommendations;
OMDb only provides display information.
"""

import os

import requests
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# Read the API key from .env (never hardcode secrets in code)
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_BASE_URL = "http://www.omdbapi.com/"

# Simple in-memory cache to avoid requesting the same movie twice
# Key example: ("avatar", "2009")
_movie_cache = {}

# OMDb uses "N/A" when a field is missing
OMDB_NOT_AVAILABLE = "N/A"


def get_cache_key(title, year=None):
    """
    Build a cache key from movie title and year.

    Args:
        title (str): Movie title.
        year (str, optional): Release year.

    Returns:
        tuple: Cache key used by the in-memory cache.
    """
    clean_title = title.strip().lower()
    clean_year = str(year).strip() if year else ""
    return (clean_title, clean_year)


def build_default_response(success=False, message=""):
    """
    Create a default response dictionary with empty OMDb fields.

    Args:
        success (bool): Whether the OMDb request succeeded.
        message (str): Error or info message.

    Returns:
        dict: Standard response format for OMDb data.
    """
    return {
        "success": success,
        "message": message,
        "poster": "",
        "rating": OMDB_NOT_AVAILABLE,
        "genre": OMDB_NOT_AVAILABLE,
        "plot": OMDB_NOT_AVAILABLE,
        "runtime": OMDB_NOT_AVAILABLE,
        "released": OMDB_NOT_AVAILABLE,
        "director": OMDB_NOT_AVAILABLE,
        "language": OMDB_NOT_AVAILABLE,
    }


def parse_omdb_response(api_data):
    """
    Convert raw OMDb JSON into our standard response format.

    Args:
        api_data (dict): JSON response from OMDb.

    Returns:
        dict: Parsed movie details.
    """
    poster = api_data.get("Poster", "")

    # OMDb returns "N/A" when there is no poster image
    if poster == OMDB_NOT_AVAILABLE:
        poster = ""

    return {
        "success": True,
        "message": "",
        "poster": poster,
        "rating": api_data.get("imdbRating", OMDB_NOT_AVAILABLE),
        "genre": api_data.get("Genre", OMDB_NOT_AVAILABLE),
        "plot": api_data.get("Plot", OMDB_NOT_AVAILABLE),
        "runtime": api_data.get("Runtime", OMDB_NOT_AVAILABLE),
        "released": api_data.get("Released", OMDB_NOT_AVAILABLE),
        "director": api_data.get("Director", OMDB_NOT_AVAILABLE),
        "language": api_data.get("Language", OMDB_NOT_AVAILABLE),
    }


def get_movie_details(title, year=None):
    """
    Fetch movie details from the OMDb API using title and optional year.

    Uses a simple in-memory cache so repeated requests are faster.

    Args:
        title (str): Movie title to search for.
        year (str, optional): Release year to improve search accuracy.

    Returns:
        dict: Movie details or a beginner-friendly error response.
    """
    if not title or not title.strip():
        response = build_default_response(
            success=False,
            message="Movie title is required.",
        )
        return response

    cache_key = get_cache_key(title, year)

    # Return cached data if this movie was already requested
    if cache_key in _movie_cache:
        return _movie_cache[cache_key]

    # Check that the API key exists
    if not OMDB_API_KEY:
        response = build_default_response(
            success=False,
            message="OMDb API key is missing. Add OMDB_API_KEY to your .env file.",
        )
        _movie_cache[cache_key] = response
        return response

    # Build the OMDb request URL and parameters
    params = {
        "apikey": OMDB_API_KEY,
        "t": title.strip(),
        "plot": "short",
    }

    # Adding the year helps OMDb return the correct movie
    if year and str(year).strip():
        params["y"] = str(year).strip()

    try:
        # Send GET request to OMDb
        api_response = requests.get(
            OMDB_BASE_URL,
            params=params,
            timeout=10,
        )
        api_response.raise_for_status()
        api_data = api_response.json()

    except requests.exceptions.Timeout:
        response = build_default_response(
            success=False,
            message="OMDb request timed out. Please try again.",
        )
        _movie_cache[cache_key] = response
        return response

    except requests.exceptions.ConnectionError:
        response = build_default_response(
            success=False,
            message="Internet connection unavailable. Please check your network.",
        )
        _movie_cache[cache_key] = response
        return response

    except requests.exceptions.RequestException:
        response = build_default_response(
            success=False,
            message="OMDb service is unavailable right now. Please try again later.",
        )
        _movie_cache[cache_key] = response
        return response

    # OMDb returns Response = "False" when something goes wrong
    if api_data.get("Response") == "False":
        error_message = api_data.get("Error", "Movie not found on OMDb.")

        if "Invalid API key" in error_message:
            error_message = "Invalid OMDb API key. Please check your .env file."

        response = build_default_response(
            success=False,
            message=error_message,
        )
        _movie_cache[cache_key] = response
        return response

    # Convert successful OMDb response to our format
    response = parse_omdb_response(api_data)
    _movie_cache[cache_key] = response
    return response
