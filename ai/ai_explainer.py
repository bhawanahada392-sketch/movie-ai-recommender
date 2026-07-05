"""
ai_explainer.py - Optional movie explanation helper.

This module talks to Google Gemini after normal recommendations are ready.
If anything goes wrong, it returns an empty string so the website can keep
showing movie recommendations without crashing.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load secrets from the project's .env file.
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Keep the LLM input small and focused so the response is fast and relevant.
MAX_PLOTS_FOR_PROMPT = 3
MAX_PLOT_CHARACTERS = 220


def get_api_key_preview(api_key):
    """
    Show only a tiny safe preview of the API key for debugging.

    Args:
        api_key (str): Gemini API key loaded from .env.

    Returns:
        str: First 6 characters only, or a missing-key label.
    """
    if not api_key:
        return "no"

    return f"yes (first 6 chars: {api_key[:6]})"


def print_gemini_error(api_data, model_name):
    """
    Print the exact Gemini error message when the response contains one.

    Args:
        api_data (dict): JSON returned by Gemini.
        model_name (str): Gemini model requested by the app.
    """
    error_data = api_data.get("error")

    if not error_data:
        return

    error_message = error_data.get("message", "No error message provided.")
    error_status = error_data.get("status", "")

    print(f"Gemini error message: {error_message}")

    if error_status:
        print(f"Gemini error status: {error_status}")

    if "not found" in error_message.lower():
        print(f"Model not found: {model_name}")


def clean_text(value, fallback="Not available"):
    """
    Convert missing values into friendly text.

    Args:
        value (str): Text from the recommendation or OMDb data.
        fallback (str): Text to use when the value is empty.

    Returns:
        str: Clean text that is safe to place inside the prompt.
    """
    if not value or value == "N/A":
        return fallback

    return str(value).strip()


def shorten_plot(plot_text):
    """
    Keep plot summaries brief before sending them to Gemini.

    Args:
        plot_text (str): Plot text from OMDb.

    Returns:
        str: Short plot text that keeps the prompt compact.
    """
    clean_plot = clean_text(plot_text)

    if len(clean_plot) <= MAX_PLOT_CHARACTERS:
        return clean_plot

    return clean_plot[:MAX_PLOT_CHARACTERS].rsplit(" ", 1)[0] + "..."


def build_movie_context(recommendations):
    """
    Turn recommendation dictionaries into short prompt notes.

    Args:
        recommendations (list): Existing enriched recommendation data.

    Returns:
        str: Compact movie notes for Gemini.
    """
    movie_notes = []

    for index, movie in enumerate(recommendations):
        title = clean_text(movie.get("title"), "Untitled movie")
        genres = clean_text(movie.get("genre"))

        note = (
            f"- Title: {title}\n"
            f"  Genres: {genres}"
        )

        # Include only the first few short plot summaries to reduce prompt size.
        if index < MAX_PLOTS_FOR_PROMPT:
            plot = shorten_plot(movie.get("plot"))
            note += f"\n  Short plot summary: {plot}"

        movie_notes.append(note)

    return "\n".join(movie_notes)


def build_explanation_prompt(searched_movie, recommendations):
    """
    Create the exact instruction sent to Gemini.

    Args:
        searched_movie (str): Movie title typed by the user.
        recommendations (list): Enriched recommendations shown on the page.

    Returns:
        str: Prompt asking for a short no-spoiler explanation.
    """
    movie_context = build_movie_context(recommendations)

    return f"""
The user searched for: {clean_text(searched_movie, "a movie")}

Top recommended movies:
{movie_context}

Write one friendly explanation for a movie discovery section titled
"Why You'll Love These".

Requirements:
- Write exactly one concise paragraph between 80 and 120 words
- Warm, conversational tone
- No spoilers
- Mention common themes, mood, and audience
- Explain why these recommendations fit together
- Do not use bullet points
- Do not mention recommendation technology or data sources
- Stop once the explanation is complete
""".strip()


def parse_gemini_text(api_data):
    """
    Read Gemini's text from the response JSON.

    Args:
        api_data (dict): JSON returned by Gemini.

    Returns:
        str: Generated explanation, or an empty string if missing.
    """
    candidates = api_data.get("candidates", [])

    if not candidates:
        return ""

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])

    if not parts:
        return ""

    explanation = parts[0].get("text", "")
    return explanation.strip()


def generate_movie_explanation(searched_movie, recommendations):
    """
    Ask Gemini why the recommendations fit together.

    Args:
        searched_movie (str): Movie title typed by the user.
        recommendations (list): Enriched recommendations shown on the page.

    Returns:
        str: Explanation text. Empty string means "hide the section".
    """
    print(f"Gemini model being used: {GEMINI_MODEL}")
    print(f"Gemini API key loaded: {get_api_key_preview(GEMINI_API_KEY)}")

    if not GEMINI_API_KEY:
        print("Gemini explanation skipped: GEMINI_API_KEY is missing.")
        return ""

    if not recommendations:
        return ""

    prompt = build_explanation_prompt(searched_movie, recommendations)

    try:
        # The official SDK creates and sends the HTTPS request to Gemini.
        # Using a context manager closes the SDK's network resources cleanly.
        with genai.Client(api_key=GEMINI_API_KEY) as client:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=512,
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=False,
                        thinking_level="MINIMAL",
                    ),
                    http_options=types.HttpOptions(timeout=60000),
                ),
            )

        explanation = clean_text(response.text, "").strip()
        print(f"Gemini parsed explanation: {explanation}")
        return explanation

    except Exception as error:
        print(f"Gemini explanation skipped: {error}")
        return ""
