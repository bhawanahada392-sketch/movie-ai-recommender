"""
ai_picks.py - Lightweight AI recommendation layer.

This keeps the existing ML recommendation engine intact and adds an
optional Gemini-based section when the search looks regional or the ML
results are too sparse.
"""

import os
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

from api.omdb import get_movie_details

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
REGIONAL_TERMS = [
    "bollywood",
    "tollywood",
    "kollywood",
    "mollywood",
    "sandalwood",
    "bhojpuri",
    "marathi",
    "punjabi",
    "tamil",
    "telugu",
    "malayalam",
    "kannada",
    "hindi",
    "bengali",
    "bangla",
    "south indian",
]


def build_fallback_ai_pick_titles(searched_movie, recommendations):
    """Create simple, local AI-pick suggestions when Gemini is unavailable."""
    query = str(searched_movie or "").lower()

    if any(term in query for term in ["hindi", "bollywood", "tollywood", "tamil", "telugu", "malayalam", "kannada", "punjabi", "marathi", "bengali", "bangla", "south indian"]):
        return ["3 Idiots", "Baahubali: The Beginning", "Rang De Basanti", "Jai Bhim", "Kabhi Khushi Kabhie Gham"]

    if any(term in query for term in ["horror", "scary", "spooky"]):
        return ["The Others", "Get Out", "The Babadook", "A Quiet Place", "Hereditary"]

    if any(term in query for term in ["romantic", "love", "date"]):
        return ["The Big Sick", "About Time", "La La Land", "The Theory of Everything", "Before Sunset"]

    if any(term in query for term in ["funny", "comedy", "laugh"]):
        return ["Paddington", "Clue", "The Grand Budapest Hotel", "Little Miss Sunshine", "Palm Springs"]

    if recommendations:
        existing_titles = [str(movie.get("title") or "").strip() for movie in recommendations[:6] if movie.get("title")]
        if existing_titles:
            return [
                "Interstellar",
                "The Matrix",
                "Arrival",
                "The Grand Budapest Hotel",
                "Spirited Away",
            ]

    return ["Interstellar", "Spirited Away", "Arrival", "The Grand Budapest Hotel", "Little Women"]


def should_generate_ai_picks(searched_movie, recommendations):
    """Decide whether an AI picks section is likely to help."""
    query = str(searched_movie or "").lower()

    if any(term in query for term in REGIONAL_TERMS):
        return True

    if not recommendations:
        return False

    return len(recommendations) < 5


def build_ai_picks_prompt(searched_movie, recommendations):
    """Ask Gemini for a short list of movie titles that fit the search."""
    context_lines = []

    for movie in recommendations[:6]:
        title = str(movie.get("title") or "Untitled movie").strip()
        year = str(movie.get("year") or "").strip()
        genres = str(movie.get("genre") or "").strip()
        plot = str(movie.get("plot") or "").strip()
        context_lines.append(
            f"- {title} ({year}) | Genres: {genres} | Plot: {plot}"
        )

    context_text = "\n".join(context_lines) if context_lines else "No recommendations available."

    return f"""
You are a movie curation assistant.
The user searched for: {searched_movie}
The main recommendation results are:
{context_text}

Suggest 5 more movie titles that genuinely fit the same themes, mood, language,
country, audience, and storytelling style.
Return only 5 movie titles, one per line, no bullets, no explanations.
""".strip()


def parse_ai_pick_titles(text):
    """Turn Gemini output into a clean list of movie titles."""
    titles = []

    for raw_line in str(text or "").splitlines():
        cleaned = re.sub(r"^\s*[-*0-9.]+\s*", "", raw_line).strip()
        cleaned = cleaned.strip(" \"'")

        if not cleaned or len(cleaned) < 2:
            continue

        if cleaned.lower() in {"none", "n/a"}:
            continue

        titles.append(cleaned)

    return titles[:5]


def call_gemini(prompt):
    """Run the Gemini API with a simple config that tolerates older SDKs."""
    if not GEMINI_API_KEY:
        return ""

    try:
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            config_kwargs = {
                "temperature": 0.7,
                "max_output_tokens": 240,
            }

            try:
                config = types.GenerateContentConfig(
                    **config_kwargs,
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=False,
                        thinking_level="MINIMAL",
                    ),
                    http_options=types.HttpOptions(timeout=30000),
                )
            except Exception:
                config = types.GenerateContentConfig(
                    **config_kwargs,
                    http_options=types.HttpOptions(timeout=30000),
                )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

        text = getattr(response, "text", "")
        return str(text or "").strip()
    except Exception as error:
        print(f"AI picks skipped: {error}")
        return ""


def generate_ai_picks(searched_movie, recommendations):
    """Generate an optional AI picks section using Gemini and OMDb metadata."""
    if not should_generate_ai_picks(searched_movie, recommendations):
        return []

    prompt = build_ai_picks_prompt(searched_movie, recommendations)
    response_text = call_gemini(prompt)
    titles = parse_ai_pick_titles(response_text)

    if not titles:
        titles = build_fallback_ai_pick_titles(searched_movie, recommendations)

    if not titles:
        return []

    ai_picks = []
    seen = set()

    for title in titles:
        key = title.lower()
        if key in seen:
            continue

        seen.add(key)

        omdb_data = get_movie_details(title, "")
        movie_details = {
            "title": title,
            "year": "",
            "similarity_score": 0.87,
            "poster": "",
            "rating": "N/A",
            "genre": "N/A",
            "plot": "N/A",
            "runtime": "N/A",
            "released": "N/A",
            "director": "N/A",
            "language": "N/A",
            "recommendation_reason": "AI pick chosen to match the mood and storytelling style of your search.",
        }

        if omdb_data.get("success"):
            movie_details["poster"] = omdb_data.get("poster", "")
            movie_details["rating"] = omdb_data.get("rating", "N/A")
            movie_details["genre"] = omdb_data.get("genre", "N/A")
            movie_details["plot"] = omdb_data.get("plot", "N/A")
            movie_details["runtime"] = omdb_data.get("runtime", "N/A")
            movie_details["released"] = omdb_data.get("released", "N/A")
            movie_details["director"] = omdb_data.get("director", "N/A")
            movie_details["language"] = omdb_data.get("language", "N/A")
            movie_details["year"] = omdb_data.get("year", "") or ""

        ai_picks.append(movie_details)

        if len(ai_picks) == 5:
            break

    return ai_picks
