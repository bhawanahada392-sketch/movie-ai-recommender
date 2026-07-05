"""
chat_agent.py - Gemini-powered movie companion chat.

The chat endpoint uses Gemini for friendly no-spoiler answers. If Gemini is
unavailable, the route returns a friendly error message instead of a broken UI.
"""

import os
import traceback

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def build_chat_prompt(question, movie=None):
    """
    Create a no-spoiler chat prompt.

    Args:
        question (str): User question.
        movie (dict): Optional movie context.

    Returns:
        str: Prompt for Gemini.
    """
    movie_context = ""

    if movie:
        movie_context = (
            f"Movie title: {movie.get('title', 'Unknown')}\n"
            f"Genre: {movie.get('genre', 'N/A')}\n"
            f"Runtime: {movie.get('runtime', 'N/A')}\n"
            f"Plot: {movie.get('plot', 'N/A')}\n"
        )

    return f"""
You are a friendly movie companion.
Answer the user's question without spoilers.
Keep the answer short, helpful, and safe for casual movie discovery.

{movie_context}
User question: {question}
""".strip()


def answer_movie_question(question, movie=None):
    """
    Ask Gemini a movie question.

    Args:
        question (str): User question.
        movie (dict): Optional movie details.

    Returns:
        str: Gemini answer, or empty string on failure.
    """
    if not GEMINI_API_KEY:
        print("Chat skipped: GEMINI_API_KEY is missing.")
        return ""

    prompt = build_chat_prompt(question, movie)

    try:
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            try:
                config = types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=180,
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=False,
                        thinking_level="MINIMAL",
                    ),
                    http_options=types.HttpOptions(timeout=30000),
                )
            except Exception as config_error:
                print(f"Chat config warning: {config_error}")
                config = types.GenerateContentConfig(
                    temperature=0.6,
                    max_output_tokens=180,
                    http_options=types.HttpOptions(timeout=30000),
                )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )

        answer = str(getattr(response, "text", "") or "").strip()
        return answer

    except Exception as error:
        print(f"Chat error: {error}")
        traceback.print_exc()
        return ""
