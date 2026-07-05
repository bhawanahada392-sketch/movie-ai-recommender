"""
recommender.py - Generate movie recommendations using trained models.

This module loads the dataset and saved models ONCE when imported,
then uses cosine similarity to recommend similar movies.
"""

import os
import pickle
import sys

import pandas as pd

# Folder paths (project root is one level above ml/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

DATA_FILE = os.path.join(DATA_DIR, "processed_movies.csv")
SIMILARITY_FILE = os.path.join(MODELS_DIR, "similarity.pkl")
VECTORIZER_FILE = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")

# Module-level variables store loaded data in memory
# Loading once avoids reading files again on every recommendation request
movies_df = None
similarity_matrix = None
tfidf_vectorizer = None
resources_loaded = False


def load_resources():
    """
    Load the processed dataset and trained model files from disk.

    This function is called once when the module is imported.
    Keeping data in memory improves performance because reading
    large files from disk on every search would be slow.

    Returns:
        bool: True if all resources loaded successfully, else False.
    """
    global movies_df, similarity_matrix, tfidf_vectorizer, resources_loaded

    print("Loading recommendation resources...")

    # Check that the dataset file exists
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: Dataset not found: {DATA_FILE}")
        print("Please run preprocess.py first.")
        resources_loaded = False
        return False

    # Check that both model files exist
    if not os.path.exists(SIMILARITY_FILE):
        print(f"ERROR: Similarity file not found: {SIMILARITY_FILE}")
        print("Please run train_model.py first.")
        resources_loaded = False
        return False

    if not os.path.exists(VECTORIZER_FILE):
        print(f"ERROR: Vectorizer file not found: {VECTORIZER_FILE}")
        print("Please run train_model.py first.")
        resources_loaded = False
        return False

    # Load the processed movie dataset
    movies_df = pd.read_csv(DATA_FILE)

    if len(movies_df) == 0:
        print("ERROR: The dataset is empty.")
        resources_loaded = False
        return False

    # Load the saved similarity matrix using pickle
    with open(SIMILARITY_FILE, "rb") as file:
        similarity_matrix = pickle.load(file)

    # Load the saved TF-IDF vectorizer using pickle
    with open(VECTORIZER_FILE, "rb") as file:
        tfidf_vectorizer = pickle.load(file)

    resources_loaded = True
    print(f"Loaded {len(movies_df)} movies successfully.")
    return True


def find_movie_index(movie_title):
    """
    Find the row index of a movie in the dataset.

    Search is case-insensitive (Avatar = avatar = AVATAR).
    If duplicate titles exist, the first match is used.

    Args:
        movie_title (str): The movie title to search for.

    Returns:
        int or None: Row index if found, else None.
    """
    # Convert search title and all titles to lowercase for comparison
    search_title = movie_title.strip().lower()

    matching_rows = movies_df[
        movies_df["title"].str.lower() == search_title
    ]

    if len(matching_rows) == 0:
        return None

    # If duplicate titles exist, use the first row
    if len(matching_rows) > 1:
        print(
            f"Note: Found {len(matching_rows)} movies titled "
            f"'{movie_title}'. Using the first match."
        )

    # Return the index of the first matching row
    return matching_rows.index[0]


def format_year(year_value):
    """
    Convert a year value from the CSV into a clean string.

    Args:
        year_value: Year from the dataset (may be missing).

    Returns:
        str: Year as text, or empty string if missing.
    """
    if pd.isna(year_value) or year_value == "":
        return ""

    try:
        return str(int(float(year_value)))
    except (ValueError, TypeError):
        return str(year_value).strip()


def build_recommendation_list(movie_index, number_of_movies):
    """
    Build a list of top similar movies for a given movie index.

    Args:
        movie_index (int): Index of the searched movie in the dataset.
        number_of_movies (int): How many recommendations to return.

    Returns:
        list: List of recommendation dictionaries with id, title, year, score.
    """
    # Get similarity scores for this movie against all other movies
    similarity_scores = similarity_matrix[movie_index]

    # Sort movie indices from highest to lowest similarity
    # argsort gives ascending order, [::-1] reverses it to descending
    sorted_indices = similarity_scores.argsort()[::-1]

    recommendations = []

    for index in sorted_indices:
        # Skip the searched movie itself (similarity with itself is 1.0)
        if index == movie_index:
            continue

        movie_id = int(movies_df.loc[index, "id"])
        title = movies_df.loc[index, "title"]
        score = round(float(similarity_scores[index]), 2)

        # Include year when available (helps OMDb find the correct movie)
        year = ""
        if "year" in movies_df.columns:
            year = format_year(movies_df.loc[index, "year"])

        recommendations.append(
            {
                "id": movie_id,
                "title": title,
                "year": year,
                "similarity_score": score,
            }
        )

        # Stop once we have enough recommendations
        if len(recommendations) == number_of_movies:
            break

    return recommendations


def recommend_movies(movie_title, number_of_movies=10):
    """
    Recommend similar movies for a given movie title.

    Args:
        movie_title (str): The movie the user searched for.
        number_of_movies (int): How many recommendations to return.

    Returns:
        dict: Result with success flag, message, and recommendations list.
    """
    # Check that resources were loaded successfully
    if not resources_loaded:
        return {
            "success": False,
            "message": (
                "Resources not loaded. Please run preprocess.py and "
                "train_model.py first."
            ),
            "recommendations": [],
        }

    # Check for empty search input
    if not movie_title or not movie_title.strip():
        return {
            "success": False,
            "message": "Please enter a movie title.",
            "recommendations": [],
        }

    # Find the movie in the dataset
    movie_index = find_movie_index(movie_title)

    if movie_index is None:
        return {
            "success": False,
            "message": "Movie not found.",
            "recommendations": [],
        }

    # Get the actual title from the dataset (correct capitalization)
    actual_title = movies_df.loc[movie_index, "title"]

    # Build and return the recommendation list
    recommendations = build_recommendation_list(
        movie_index, number_of_movies
    )

    return {
        "success": True,
        "movie": actual_title,
        "recommendations": recommendations,
    }


# Load all resources ONCE when this file is imported (not on every call)
load_resources()


# Simple test when this file is run directly
if __name__ == "__main__":
    print("\n--- Testing Movie Recommendations ---\n")

    test_title = "Avatar"
    result = recommend_movies(test_title)

    if result["success"]:
        print(f"Recommendations for: {result['movie']}\n")
        for rank, movie in enumerate(result["recommendations"], start=1):
            print(
                f"{rank}. {movie['title']} "
                f"(ID: {movie['id']}, "
                f"Year: {movie.get('year', '')}, "
                f"Score: {movie['similarity_score']})"
            )
    else:
        print(f"Error: {result['message']}")
