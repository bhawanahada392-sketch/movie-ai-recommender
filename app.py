"""
app.py - Main entry point for the Flask web application.

This file creates the Flask app, serves the homepage,
connects the ML recommendation engine with OMDb movie details.
"""

import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, render_template, request

from ai.ai_picks import generate_ai_picks
from ai.bollywood_rerank import rerank_indian_recommendations
from ai.chat_agent import answer_movie_question
from ai.collections import get_collection_movies, list_collections
from ai.dynamic_cache import get_or_fetch_dynamic_movie
from ai.explanation_agent import (
    add_individual_reasons,
    generate_overview_explanation,
)
from ai.intent_agent import extract_intent
from ai.ranking_agent import rank_recommendations
from ai.recent_searches import (
    add_recent_search,
    clear_recent_searches,
    get_recent_searches,
)
from ai.recommendation_agent import (
    get_recommendations_for_intent,
    search_dataset_by_intent,
)
from ai.search_agent import rewrite_search_query
from api.omdb import get_movie_details
from api.tmdb import discover_homepage_rows, search_movies

# Create the Flask application instance
# __name__ tells Flask where to find templates and static files
app = Flask(__name__)

# OMDb requests are network-bound, so a small thread pool can fetch several
# movie detail pages at the same time without changing recommendation order.
OMDB_WORKER_COUNT = 5


@app.route("/")
def home():
    """Render the minimal home page with discover rows."""
    rows = discover_homepage_rows()
    return render_template("index.html", homepage_rows=rows)


@app.route("/results")
def results_page():
    """Render the dedicated results page."""
    query = request.args.get("q", "").strip()
    return render_template("results.html", query=query)


@app.route("/watchlist-page")
def watchlist_page():
    """Render the dedicated watchlist page."""
    return render_template("watchlist.html")


@app.route("/history-page")
def history_page():
    """Render the dedicated history page."""
    return render_template("history.html")


@app.route("/ai-companion")
def ai_companion_page():
    """Render the dedicated AI companion page."""
    return render_template("ai_companion.html")


@app.route("/collections-page")
def collections_page():
    """Render the dedicated collections page."""
    return render_template("collections.html")


def enrich_single_recommendation(recommendation):
    """
    Add OMDb details to one recommendation dictionary.

    Args:
        recommendation (dict): One movie from the ML recommendation list.

    Returns:
        dict: Recommendation merged with the same OMDb fields as before.
    """
    title = recommendation["title"]
    year = recommendation.get("year", "")

    # Fetch OMDb details using title and year.
    # get_movie_details still uses the existing in-memory cache.
    omdb_data = get_movie_details(title, year)

    # Start with ML recommendation data
    movie_details = {
        "title": title,
        "year": year,
        "similarity_score": recommendation["similarity_score"],
        "poster": "",
        "rating": "N/A",
        "genre": "N/A",
        "plot": "N/A",
        "runtime": "N/A",
        "released": "N/A",
        "director": "N/A",
        "language": "N/A",
    }

    # Merge OMDb fields when the API call succeeds
    if omdb_data.get("success"):
        movie_details["poster"] = omdb_data.get("poster", "")
        movie_details["rating"] = omdb_data.get("rating", "N/A")
        movie_details["genre"] = omdb_data.get("genre", "N/A")
        movie_details["plot"] = omdb_data.get("plot", "N/A")
        movie_details["runtime"] = omdb_data.get("runtime", "N/A")
        movie_details["released"] = omdb_data.get("released", "N/A")
        movie_details["director"] = omdb_data.get("director", "N/A")
        movie_details["language"] = omdb_data.get("language", "N/A")
    else:
        # Keep ML recommendation even if OMDb fails for one movie
        movie_details["omdb_message"] = omdb_data.get(
            "message",
            "Movie details unavailable.",
        )

    return movie_details


def enrich_recommendations(recommendations):
    """
    Add OMDb movie details to each ML recommendation.

    The ML model still chooses WHICH movies to recommend.
    OMDb only adds poster, rating, plot, and other display info.

    Args:
        recommendations (list): List of ML recommendation dictionaries.

    Returns:
        list: Recommendations merged with OMDb details.
    """
    if not recommendations:
        return []

    worker_count = min(OMDB_WORKER_COUNT, len(recommendations))

    # executor.map returns results in the same order as the input list.
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        enriched_list = list(
            executor.map(enrich_single_recommendation, recommendations)
        )

    return enriched_list


def improve_intent_with_dynamic_movie(intent):
    """
    Use OMDb metadata for titles that are not in the local dataset.

    Args:
        intent (dict): Parsed user intent.

    Returns:
        dict: Updated intent with extra genre/keyword hints when available.
    """
    movie_title = intent.get("movie_title", "")

    if not movie_title or intent.get("exact_movie_title"):
        return intent

    # Natural-language requests should use dataset intent search instead of
    # trying to fetch phrases like "Movie under 2 hours" from OMDb.
    if (
        intent.get("genre")
        or intent.get("mood")
        or intent.get("occasion")
        or intent.get("runtime_preference")
    ):
        return intent

    metadata = get_or_fetch_dynamic_movie(movie_title)

    if not metadata:
        return intent

    genre_text = metadata.get("genre", "")
    plot_text = metadata.get("plot", "")

    for genre in genre_text.split(","):
        clean_genre = genre.strip().lower()
        if clean_genre and clean_genre not in intent["genre"]:
            intent["genre"].append(clean_genre)

    for word in plot_text.lower().split():
        clean_word = word.strip(".,!?;:")
        if len(clean_word) > 4 and clean_word not in intent["keywords"]:
            intent["keywords"].append(clean_word)

    return intent


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Recommendation API route.

    Receives a movie name as JSON, calls the ML model,
    enriches results with OMDb data, and returns JSON.
    """
    total_start_time = time.perf_counter()

    try:
        # request.get_json() reads JSON data sent from the browser
        data = request.get_json()

        # Validate that JSON data was received
        if data is None:
            total_duration = time.perf_counter() - total_start_time
            print(f"Timing - Total request: {total_duration:.2f}s")
            return jsonify(
                {
                    "success": False,
                    "message": "Please enter a movie name.",
                }
            )

        # Get the movie name from JSON and remove extra spaces
        movie = data.get("movie", "").strip()

        # Validate that the movie name is not empty
        if not movie:
            total_duration = time.perf_counter() - total_start_time
            print(f"Timing - Total request: {total_duration:.2f}s")
            return jsonify(
                {
                    "success": False,
                    "message": "Please enter a movie name.",
                }
            )

        # Print useful logs in the Flask terminal
        print(f"Movie searched: {movie}")
        add_recent_search(movie)

        # Step 1: Understand the title or natural-language request.
        intent = extract_intent(movie)
        intent = improve_intent_with_dynamic_movie(intent)

        # Step 2: Decide whether this is a known dataset title or
        # a broader mood/genre request that should query TMDb.
        result = None
        tmdb_query = None
        if intent.get("exact_movie_title") or intent.get("movie_title"):
            ml_start_time = time.perf_counter()
            result = get_recommendations_for_intent(intent)
            ml_duration = time.perf_counter() - ml_start_time
            print(f"Timing - ML recommendation: {ml_duration:.2f}s")

            if not result.get("success") and intent.get("keywords"):
                ml_start_time = time.perf_counter()
                result = search_dataset_by_intent(intent)
                ml_duration = time.perf_counter() - ml_start_time
                print(f"Timing - ML fallback keyword search: {ml_duration:.2f}s")
        else:
            tmdb_query = rewrite_search_query(movie)
            tmdb_movies = search_movies(tmdb_query or movie)

            if tmdb_movies:
                return jsonify(
                    {
                        "success": True,
                        "movie": movie,
                        "recommendations": tmdb_movies,
                        "ai_explanation": "Results are matched from TMDb using your mood, genre, or description.",
                    }
                )

            ml_start_time = time.perf_counter()
            result = search_dataset_by_intent(intent)
            ml_duration = time.perf_counter() - ml_start_time
            print(f"Timing - ML fallback intent search: {ml_duration:.2f}s")

        if not result.get("success"):
            print(f"Search failed: {result.get('message')}")
            total_duration = time.perf_counter() - total_start_time
            print(f"Timing - Total request: {total_duration:.2f}s")
            return jsonify(result)

        # Step 3: OMDb adds poster, rating, plot, etc. for each movie
        omdb_start_time = time.perf_counter()
        enriched_recommendations = enrich_recommendations(
            result.get("recommendations", [])
        )
        omdb_duration = time.perf_counter() - omdb_start_time
        print(f"Timing - OMDb enrichment: {omdb_duration:.2f}s")

        # Step 4: Rank enriched movies and add one reason per movie.
        ranked_recommendations = rank_recommendations(
            enriched_recommendations,
            intent,
        )[:10]
        searched_title = result.get("resolved_title") or result.get("movie") or movie

        ranked_recommendations = rerank_indian_recommendations(
            ranked_recommendations,
            searched_title,
        )

        ranked_recommendations = add_individual_reasons(
            searched_title,
            ranked_recommendations,
            intent,
        )

        result["recommendations"] = ranked_recommendations

        ai_picks = generate_ai_picks(movie, ranked_recommendations)
        if ai_picks:
            result["ai_picks"] = ai_picks

        # Step 5: Optionally add a friendly explanation.
        # If Gemini is unavailable, this returns an empty string and
        # recommendations still display normally.
        gemini_start_time = time.perf_counter()
        ai_explanation = generate_overview_explanation(
            searched_title,
            ranked_recommendations,
        )
        gemini_duration = time.perf_counter() - gemini_start_time
        print(f"Timing - Gemini generation: {gemini_duration:.2f}s")

        if ai_explanation:
            result["ai_explanation"] = ai_explanation

        count = len(ranked_recommendations)
        print(f"Recommendations returned: {count}")
        total_duration = time.perf_counter() - total_start_time
        print(f"Timing - Total request: {total_duration:.2f}s")

        # jsonify() converts a Python dictionary into JSON for the browser
        return jsonify(result)

    except Exception as error:
        # Handle unexpected errors with a friendly message
        print(f"Error in /recommend: {error}")
        total_duration = time.perf_counter() - total_start_time
        print(f"Timing - Total request: {total_duration:.2f}s")
        return jsonify(
            {
                "success": False,
                "message": "Something went wrong. Please try again.",
            }
        )


@app.route("/watchlist", methods=["GET"])
def watchlist_get():
    """
    Return the current in-memory watchlist.
    """
    return jsonify(
        {
            "success": True,
            "watchlist": get_watchlist(),
        }
    )


@app.route("/watchlist/add", methods=["POST"])
def watchlist_add():
    """
    Add one movie to the in-memory watchlist.
    """
    data = request.get_json() or {}
    movie = data.get("movie", data)
    watchlist = add_to_watchlist(movie)

    return jsonify(
        {
            "success": True,
            "watchlist": watchlist,
        }
    )


@app.route("/watchlist/remove", methods=["POST"])
def watchlist_remove():
    """
    Remove one movie from the in-memory watchlist.
    """
    data = request.get_json() or {}
    movie = data.get("movie", data)
    watchlist = remove_from_watchlist(movie)

    return jsonify(
        {
            "success": True,
            "watchlist": watchlist,
        }
    )


@app.route("/watchlist/clear", methods=["POST"])
def watchlist_clear():
    """
    Clear the in-memory watchlist.
    """
    return jsonify(
        {
            "success": True,
            "watchlist": clear_watchlist(),
        }
    )


@app.route("/recent-searches", methods=["GET"])
def recent_searches_get():
    """
    Return recent searches.
    """
    return jsonify(
        {
            "success": True,
            "recent_searches": get_recent_searches(),
        }
    )


@app.route("/recent-searches/add", methods=["POST"])
def recent_searches_add():
    """
    Add one recent search.
    """
    data = request.get_json() or {}
    query = data.get("query", "")

    return jsonify(
        {
            "success": True,
            "recent_searches": add_recent_search(query),
        }
    )


@app.route("/recent-searches/clear", methods=["POST"])
def recent_searches_clear():
    """
    Clear recent searches.
    """
    return jsonify(
        {
            "success": True,
            "recent_searches": clear_recent_searches(),
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    """
    Answer simple no-spoiler movie questions with Gemini.
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    movie = data.get("movie")
    title = data.get("title", "").strip()

    if not question:
        return jsonify(
            {
                "success": False,
                "message": "Please enter a question.",
                "answer": "",
            }
        )

    if not movie and title:
        movie_details = get_movie_details(title)
        if movie_details.get("success"):
            movie = movie_details
        else:
            movie = {"title": title}

    try:
        answer = answer_movie_question(question, movie)
    except Exception as error:
        print(f"Chat route error: {error}")
        traceback.print_exc()
        return jsonify(
            {
                "success": False,
                "message": "I'm having trouble connecting right now. Please try again.",
                "answer": "",
            }
        )

    if not answer:
        return jsonify(
            {
                "success": False,
                "message": "I'm having trouble connecting right now. Please try again.",
                "answer": "",
            }
        )

    return jsonify(
        {
            "success": True,
            "answer": answer,
        }
    )


@app.route("/collections", methods=["GET"])
def collections_get():
    """
    Return available curated collections.
    """
    return jsonify(
        {
            "success": True,
            "collections": list_collections(),
        }
    )


@app.route("/collections/<collection_slug>", methods=["GET"])
def collection_detail(collection_slug):
    """
    Return movies for one curated collection.
    """
    return jsonify(get_collection_movies(collection_slug))


# This block runs only when we execute: python app.py
if __name__ == "__main__":
    app.run(debug=True)
