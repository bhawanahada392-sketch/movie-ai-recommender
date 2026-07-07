"""
recommender.py - Generate movie recommendations using trained models.

This module loads the dataset and saved models ONCE when imported,
then uses cosine similarity to recommend similar movies.
"""

import os
import pickle
import sys

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

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
tfidf_matrix = None
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
    global movies_df, similarity_matrix, tfidf_matrix, tfidf_vectorizer, resources_loaded

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

    # Load either the old full similarity matrix or the new smaller TF-IDF
    # matrix format. This keeps older model files readable.
    with open(SIMILARITY_FILE, "rb") as file:
        saved_similarity_data = pickle.load(file)

    if isinstance(saved_similarity_data, dict):
        tfidf_matrix = saved_similarity_data.get("matrix")
        similarity_matrix = None
    else:
        similarity_matrix = saved_similarity_data
        tfidf_matrix = None

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


def clean_display_value(value):
    """Return a simple display string for optional dataset fields."""
    if pd.isna(value) or value == "":
        return ""

    return str(value).strip()


def row_metadata_score(row):
    """Score metadata richness so complete rows win close similarity ties."""
    score = 0

    for column, points in [
        ("poster", 6),
        ("overview", 5),
        ("genres", 4),
        ("cast", 3),
        ("director", 3),
        ("keywords", 2),
        ("rating", 1),
    ]:
        if column in row and clean_display_value(row.get(column)):
            score += points

    return score


def normalize_metadata_value(value):
    """Normalize optional metadata for grouping comparisons."""
    return clean_display_value(value).lower()


def get_movie_language(row):
    """Return the dataset language value for a movie row."""
    return normalize_metadata_value(row.get("language", ""))


def get_movie_source(row):
    """Return the dataset source value for a movie row."""
    return normalize_metadata_value(row.get("source", ""))


def infer_movie_industry(row):
    """
    Infer a broad industry bucket from merged dataset metadata.

    The merged data already marks large groups through source/language:
    Bollywood and curated Indian rows are grouped as Indian, while English
    TMDb rows are treated as Hollywood candidates. Other movies fall back
    to their source or language so their recommendations still work.
    """
    source = get_movie_source(row)
    language = get_movie_language(row)

    if source == "bollywood" or (source == "curated" and language != "english"):
        return "indian"

    if source == "tmdb" and language == "english":
        return "hollywood"

    return source or language


def has_good_recommendation_metadata(row):
    """
    Check whether a candidate has enough metadata to be a useful match.

    Sparse rows can tie strongly after the merge because their feature text
    is nearly identical. We keep them as fallbacks, but prefer candidates
    with genre, plot, cast, or director information first.
    """
    for column in ["genres", "overview", "cast", "director"]:
        if column in row and clean_display_value(row.get(column)):
            return True

    return False


def build_prioritized_candidate_order(movie_index, sorted_indices, similarity_scores):
    """
    Reorder already-scored candidates using source/language metadata.

    Cosine similarity is still computed exactly once before this helper and
    remains the ranking inside each tier. The only change is that movies
    from the searched movie's language/industry are considered before the
    full cross-industry fallback list.
    """
    reference_row = movies_df.loc[movie_index]
    reference_language = get_movie_language(reference_row)
    reference_industry = infer_movie_industry(reference_row)

    if not reference_language and not reference_industry:
        return sorted_indices

    def is_same_language(index):
        return (
            reference_language
            and get_movie_language(movies_df.loc[index]) == reference_language
        )

    def is_same_industry(index):
        return (
            reference_industry
            and infer_movie_industry(movies_df.loc[index]) == reference_industry
        )

    def has_positive_score(index):
        return float(similarity_scores[index]) > 0

    def has_good_metadata(index):
        return has_good_recommendation_metadata(movies_df.loc[index])

    if reference_industry == "indian":
        tier_checks = [
            lambda index: is_same_language(index) and is_same_industry(index) and has_good_metadata(index),
            lambda index: is_same_industry(index) and has_good_metadata(index),
            lambda index: is_same_language(index) and is_same_industry(index) and has_positive_score(index),
            lambda index: is_same_industry(index) and has_positive_score(index),
        ]
    elif reference_industry == "hollywood":
        tier_checks = [
            lambda index: is_same_industry(index) and has_good_metadata(index),
            lambda index: is_same_language(index) and has_good_metadata(index),
            lambda index: is_same_industry(index) and has_positive_score(index),
            lambda index: is_same_language(index) and has_positive_score(index),
        ]
    else:
        tier_checks = [
            lambda index: is_same_language(index) and has_good_metadata(index),
            lambda index: is_same_industry(index) and has_good_metadata(index),
            lambda index: is_same_language(index) and has_positive_score(index),
            lambda index: is_same_industry(index) and has_positive_score(index),
        ]

    prioritized_indices = []
    seen_indices = set()

    for check in tier_checks:
        for index in sorted_indices:
            if index in seen_indices or index == movie_index:
                continue

            if check(index):
                prioritized_indices.append(index)
                seen_indices.add(index)

    for index in sorted_indices:
        if index not in seen_indices:
            prioritized_indices.append(index)

    return prioritized_indices


def row_to_recommendation(index, similarity_score):
    """Convert one dataframe row into the API recommendation shape."""
    row = movies_df.loc[index]

    return {
        "id": int(row["id"]),
        "title": row["title"],
        "year": format_year(row.get("year", "")),
        "similarity_score": round(float(similarity_score), 2),
        "genre": clean_display_value(row.get("genres", "")),
        "genres": clean_display_value(row.get("genres", "")),
        "plot": clean_display_value(row.get("overview", "")),
        "overview": clean_display_value(row.get("overview", "")),
        "director": clean_display_value(row.get("director", "")),
        "language": clean_display_value(row.get("language", "")),
        "poster": clean_display_value(row.get("poster", "")),
        "rating": clean_display_value(row.get("rating", "")),
    }


def build_recommendation_list(movie_index, number_of_movies):
    """
    Build a list of top similar movies for a given movie index.

    Args:
        movie_index (int): Index of the searched movie in the dataset.
        number_of_movies (int): How many recommendations to return.

    Returns:
        list: List of recommendation dictionaries with id, title, year, score.
    """
    # Get similarity scores for this movie against all other movies.
    # Newer model files calculate cosine similarity on demand from the
    # saved TF-IDF matrix. Older model files may already contain the
    # full all-vs-all similarity matrix.
    if tfidf_matrix is not None:
        similarity_scores = cosine_similarity(
            tfidf_matrix[movie_index],
            tfidf_matrix,
        ).flatten()
    else:
        similarity_scores = similarity_matrix[movie_index]

    # Sort by similarity first, then by metadata richness. This keeps the ML
    # score in charge while preferring complete movie rows when scores tie.
    sorted_indices = sorted(
        range(len(similarity_scores)),
        key=lambda index: (
            -float(similarity_scores[index]),
            -row_metadata_score(movies_df.loc[index]),
            str(movies_df.loc[index, "title"]),
        ),
    )
    candidate_indices = build_prioritized_candidate_order(
        movie_index,
        sorted_indices,
        similarity_scores,
    )

    recommendations = []
    fallback_recommendations = []

    for index in candidate_indices:
        # Skip the searched movie itself (similarity with itself is 1.0)
        if index == movie_index:
            continue

        score = round(float(similarity_scores[index]), 2)
        recommendation = row_to_recommendation(index, score)

        if score > 0:
            recommendations.append(recommendation)
        else:
            fallback_recommendations.append(recommendation)

        # Stop once we have enough recommendations
        if len(recommendations) == number_of_movies:
            break

    if len(recommendations) < number_of_movies:
        needed = number_of_movies - len(recommendations)
        recommendations.extend(fallback_recommendations[:needed])

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
