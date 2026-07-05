"""
search_agent.py - Small Gemini-backed helper for natural-language search.

This module rewrites a user query into a concise movie discovery phrase.
If Gemini is unavailable, it keeps the original query unchanged.
"""

import os
import traceback

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def build_search_prompt(user_query):
    """Build a simple Gemini prompt for user search understanding."""
    return f"""
You are a friendly movie discovery assistant.
Rewrite the user's request into a short movie search phrase.
Do not add explanation or extra detail.
If the user typed a movie title, return that title exactly.
If the user asked for mood, genre, or occasion, return a concise phrase that captures the request.
Keep the response to one or two short phrases.

User request: {user_query}
Search phrase:""".strip()


def rewrite_search_query(user_query):
    """Rewrite a natural-language query for TMDb search."""
    if not user_query or not GEMINI_API_KEY:
        return user_query

    try:
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=build_search_prompt(user_query),
                config=types.GenerateContentConfig(
                    temperature=0.45,
                    max_output_tokens=80,
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=False,
                        thinking_level="MINIMAL",
                    ),
                    http_options=types.HttpOptions(timeout=30000),
                ),
            )

        return str(getattr(response, "text", "") or "").strip()
    except Exception as error:
        print(f"Search rewrite skipped: {error}")
        traceback.print_exc()
        return user_query
