"""
tmdb.py - TMDB API helper functions.

This module fetches movie posters and movie lists from TMDb.
It supports homepage browse rows and search-based discovery.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

GENRE_IDS = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "science fiction": 878,
    "tv movie": 10770,
    "thriller": 53,
    "war": 10752,
    "western": 37,
}

ROW_CONFIGS = [
    {
        "slug": "trending",
        "label": "Trending",
        "strategy": "trending",
    },
    {
        "slug": "top_rated",
        "label": "Top Rated",
        "strategy": "top_rated",
    },
    {
        "slug": "action",
        "label": "Action",
        "strategy": "genre",
        "genre": "action",
    },
    {
        "slug": "comedy",
        "label": "Comedy",
        "strategy": "genre",
        "genre": "comedy",
    },
    {
        "slug": "romance",
        "label": "Romance",
        "strategy": "genre",
        "genre": "romance",
    },
    {
        "slug": "science_fiction",
        "label": "Science Fiction",
        "strategy": "genre",
        "genre": "science fiction",
    },
    {
        "slug": "adventure",
        "label": "Adventure",
        "strategy": "genre",
        "genre": "adventure",
    },
    {
        "slug": "indian_cinema",
        "label": "Indian Cinema",
        "strategy": "indian_cinema",
    },
]


def build_url(path):
    return f"{TMDB_BASE_URL}{path}"


def fetch_tmdb_json(path, params=None):
    if not TMDB_API_KEY:
        return {}

    params = params.copy() if params else {}
    params["api_key"] = TMDB_API_KEY
    params.setdefault("language", "en-US")

    try:
        response = requests.get(build_url(path), params=params, timeout=10)
        response.raise_for_status()
        return response.json() or {}
    except requests.RequestException:
        return {}


def build_poster_url(path):
    if not path:
        return ""
    return f"{TMDB_IMAGE_BASE}{path}"


def normalize_tmdb_movie(raw_movie):
    if not raw_movie:
        return {}

    title = raw_movie.get("title") or raw_movie.get("name") or ""
    release_date = raw_movie.get("release_date") or raw_movie.get("first_air_date") or ""
    year = ""
    if release_date:
        year = str(release_date).split("-")[0]

    return {
        "id": raw_movie.get("id"),
        "title": title,
        "year": year,
        "poster": build_poster_url(raw_movie.get("poster_path")),
        "plot": raw_movie.get("overview", "N/A"),
        "rating": str(raw_movie.get("vote_average", "N/A")) if raw_movie.get("vote_average") else "N/A",
        "genre": "N/A",
        "runtime": "N/A",
        "released": year,
        "director": "N/A",
        "language": raw_movie.get("original_language", "N/A").upper(),
        "country": "N/A",
        "similarity_score": round(float(raw_movie.get("popularity", 0) or 0) / 100, 2),
    }


def search_movies(query, limit=12):
    if not query or not TMDB_API_KEY:
        return []

    api_data = fetch_tmdb_json(
        "/search/movie",
        {
            "query": query,
            "include_adult": False,
            "page": 1,
        },
    )

    results = api_data.get("results", []) or []
    normalized = [normalize_tmdb_movie(movie) for movie in results]
    return normalized[:limit]


def discover_movies_by_genre(genre_name, limit=8):
    genre_id = GENRE_IDS.get(genre_name.lower())
    if not genre_id:
        return []

    api_data = fetch_tmdb_json(
        "/discover/movie",
        {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "vote_count.gte": 200,
            "page": 1,
        },
    )

    results = api_data.get("results", []) or []
    normalized = [normalize_tmdb_movie(movie) for movie in results]
    return normalized[:limit]


def discover_trending(limit=8):
    api_data = fetch_tmdb_json("/trending/movie/day", {"page": 1})
    results = api_data.get("results", []) or []
    normalized = [normalize_tmdb_movie(movie) for movie in results]
    return normalized[:limit]


def discover_top_rated(limit=8):
    api_data = fetch_tmdb_json(
        "/movie/top_rated",
        {
            "vote_count.gte": 1000,
            "page": 1,
        },
    )

    results = api_data.get("results", []) or []
    normalized = [normalize_tmdb_movie(movie) for movie in results]
    return normalized[:limit]


def discover_indian_cinema(limit=8):
    api_data = fetch_tmdb_json(
        "/discover/movie",
        {
            "with_origin_country": "IN",
            "sort_by": "popularity.desc",
            "vote_count.gte": 80,
            "page": 1,
        },
    )

    results = api_data.get("results", []) or []
    normalized = [normalize_tmdb_movie(movie) for movie in results]
    return normalized[:limit]


def discover_homepage_rows():
    rows = []

    for row in ROW_CONFIGS:
        if row["strategy"] == "trending":
            movies = discover_trending()
        elif row["strategy"] == "top_rated":
            movies = discover_top_rated()
        elif row["strategy"] == "genre":
            movies = discover_movies_by_genre(row["genre"])
        elif row["strategy"] == "indian_cinema":
            movies = discover_indian_cinema()
        else:
            movies = []

        if movies:
            rows.append(
                {
                    "slug": row["slug"],
                    "title": row["label"],
                    "movies": movies,
                }
            )

    return rows
