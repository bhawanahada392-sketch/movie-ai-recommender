"""
train_model.py - Train the movie recommendation model.

This script reads processed movie data, builds a TF-IDF matrix,
calculates cosine similarity between all movies, and saves the
results so recommender.py can use them without retraining.
"""

import os
import pickle
import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Folder paths (project root is one level above ml/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

DATA_FILE = os.path.join(DATA_DIR, "processed_movies.csv")
SIMILARITY_FILE = os.path.join(MODELS_DIR, "similarity.pkl")
VECTORIZER_FILE = os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl")

# Columns required for training
REQUIRED_COLUMNS = ["id", "title", "combined_features"]


def validate_columns(dataframe):
    """
    Check that all required columns exist in the dataset.

    If any column is missing, print an error and stop the program.

    Args:
        dataframe (pd.DataFrame): The loaded dataset.

    Returns:
        bool: True if all columns exist.
    """
    missing_columns = []

    for column_name in REQUIRED_COLUMNS:
        if column_name not in dataframe.columns:
            missing_columns.append(column_name)

    if missing_columns:
        print("\nERROR: The following required columns are missing:")
        for column_name in missing_columns:
            print(f"  - {column_name}")
        print("\nPlease run preprocess.py first and try again.")
        sys.exit(1)

    return True


def display_dataset_info(dataframe):
    """
    Print useful information about the dataset.

    Args:
        dataframe (pd.DataFrame): The loaded dataset.
    """
    print(f"Number of movies: {len(dataframe)}")
    print(f"Column names: {list(dataframe.columns)}")
    print(f"Dataset shape: {dataframe.shape}")


def save_models(similarity_matrix, vectorizer):
    """
    Save the trained similarity matrix and TF-IDF vectorizer to disk.

    Saving models is useful because training takes time.
    We train once and reuse the saved files many times later.

    Args:
        similarity_matrix: Cosine similarity scores between movies.
        vectorizer: Fitted TF-IDF vectorizer object.
    """
    print("\nSaving trained model...")

    # Create the models folder if it does not exist yet
    os.makedirs(MODELS_DIR, exist_ok=True)

    # pickle.dump writes a Python object to a .pkl file
    with open(SIMILARITY_FILE, "wb") as file:
        pickle.dump(similarity_matrix, file)

    with open(VECTORIZER_FILE, "wb") as file:
        pickle.dump(vectorizer, file)

    print(f"Saved similarity matrix to: {SIMILARITY_FILE}")
    print(f"Saved TF-IDF vectorizer to: {VECTORIZER_FILE}")


def main():
    """
    Run the full training pipeline from start to finish.
    """
    # STEP 1: Load the processed dataset
    print("Loading dataset...")

    if not os.path.exists(DATA_FILE):
        print(f"\nERROR: Dataset file not found: {DATA_FILE}")
        print("Please run preprocess.py first.")
        sys.exit(1)

    movies_df = pd.read_csv(DATA_FILE)

    # STEP 2: Validate required columns
    validate_columns(movies_df)

    # Check for empty dataset
    if len(movies_df) == 0:
        print("\nERROR: The dataset is empty.")
        sys.exit(1)

    # STEP 3: Print dataset information
    print("\nDataset information:")
    display_dataset_info(movies_df)

    # STEP 4: Create and fit the TF-IDF Vectorizer
    print("\nCreating TF-IDF matrix...")

    # TfidfVectorizer converts text into numeric vectors
    vectorizer = TfidfVectorizer(
        # stop_words='english' removes common words like "the", "and", "is"
        # These words appear in many movies and do not help find similar ones
        stop_words="english",
        # max_features limits how many unique words we keep (top 5000 by frequency)
        # This keeps training fast and memory usage reasonable for beginners
        max_features=5000,
    )

    # fit_transform learns vocabulary from text and converts it to numbers
    tfidf_matrix = vectorizer.fit_transform(movies_df["combined_features"])

    # STEP 5: Print TF-IDF matrix shape
    # Shape is (number_of_movies, number_of_words_in_vocabulary)
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    # STEP 6: Calculate Cosine Similarity
    print("\nCalculating cosine similarity...")

    # Cosine similarity measures how similar two movies are (0 to 1).
    # 1.0 = very similar, 0.0 = not similar at all.
    # It works well for recommendations because it compares the DIRECTION
    # of two text vectors, not their length. Two sci-fi movies with
    # similar words will have vectors pointing in a similar direction.
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    print(f"Similarity matrix shape: {similarity_matrix.shape}")

    # STEP 7: Save both trained objects to pickle files
    save_models(similarity_matrix, vectorizer)

    print("\nTraining completed successfully.")


if __name__ == "__main__":
    main()
