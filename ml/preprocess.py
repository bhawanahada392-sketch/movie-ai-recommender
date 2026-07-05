"""
preprocess.py - Data preprocessing for the movie recommendation model.

This script loads raw TMDB CSV files, cleans them, and saves
a processed file ready for TF-IDF and Cosine Similarity (next step).
"""

import ast
import os
import sys

import pandas as pd

# Paths to the data folder (one level above the ml folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

MOVIES_FILE = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
CREDITS_FILE = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "processed_movies.csv")

# Columns needed while cleaning and building combined_features
REQUIRED_COLUMNS = [
    "id",
    "title",
    "genres",
    "keywords",
    "overview",
    "cast",
    "crew",
    "release_date",
]

# Final columns saved to processed_movies.csv
FINAL_COLUMNS = [
    "id",
    "title",
    "year",
    "combined_features",
]


def load_datasets():
    """
    Load both CSV files into pandas DataFrames.

    Returns:
        tuple: (movies_df, credits_df)
    """
    print("Loading datasets...")

    # read_csv reads a CSV file and stores it as a table (DataFrame)
    movies_df = pd.read_csv(MOVIES_FILE)
    credits_df = pd.read_csv(CREDITS_FILE)

    print("Datasets loaded successfully.")
    return movies_df, credits_df


def display_dataset_info(dataframe, dataset_name):
    """
    Print basic information about a dataset.

    Args:
        dataframe (pd.DataFrame): The dataset to inspect.
        dataset_name (str): A friendly name like 'Movies' or 'Credits'.
    """
    print(f"\n--- {dataset_name} Dataset Info ---")
    print(f"Number of rows: {len(dataframe)}")
    print(f"Number of columns: {len(dataframe.columns)}")
    print(f"Column names: {list(dataframe.columns)}")


def merge_datasets(movies_df, credits_df):
    """
    Merge movies and credits into one dataset using the movie title.

    We merge because movie details (genres, overview) are in one file
    and cast/crew information is in another file. Combining them gives
    us all features we need for each movie in one row.

    Args:
        movies_df (pd.DataFrame): Movies dataset.
        credits_df (pd.DataFrame): Credits dataset.

    Returns:
        pd.DataFrame: Merged dataset.
    """
    print("\nMerging datasets...")

    # inner merge keeps only movies that exist in BOTH files
    merged_df = movies_df.merge(credits_df, on="title", how="inner")

    print(f"Merged dataset has {len(merged_df)} rows.")
    return merged_df


def validate_columns(dataframe):
    """
    Check that all required columns exist in the dataset.

    If any column is missing, print an error and stop the program.

    Args:
        dataframe (pd.DataFrame): Dataset to validate.

    Returns:
        bool: True if all columns exist, otherwise the program exits.
    """
    missing_columns = []

    for column_name in REQUIRED_COLUMNS:
        if column_name not in dataframe.columns:
            missing_columns.append(column_name)

    if missing_columns:
        print("\nERROR: The following required columns are missing:")
        for column_name in missing_columns:
            print(f"  - {column_name}")
        print("\nPlease check your CSV files and try again.")
        sys.exit(1)

    print("All required columns are present.")
    return True


def extract_names_from_json(text):
    """
    Extract 'name' values from genres or keywords JSON-like strings.

    Example input:
        '[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}]'

    Example output:
        'Action Adventure'

    Args:
        text (str): JSON-like string from the CSV.

    Returns:
        str: Space-separated names.
    """
    if pd.isna(text) or text == "":
        return ""

    try:
        # ast.literal_eval safely converts a string to a Python list/dict.
        # It is safer than eval() because eval() can run harmful code.
        items = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return ""

    names = []
    for item in items:
        if isinstance(item, dict) and "name" in item:
            names.append(item["name"])

    return " ".join(names)


def extract_cast_names(text, max_actors=3):
    """
    Extract the first few actor names from the cast column.

    Example output for Avatar:
        'Sam Worthington Zoe Saldana Sigourney Weaver'

    Args:
        text (str): JSON-like cast string from the CSV.
        max_actors (int): How many actors to keep (default 3).

    Returns:
        str: Space-separated actor names.
    """
    if pd.isna(text) or text == "":
        return ""

    try:
        items = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return ""

    names = []
    for item in items[:max_actors]:
        if isinstance(item, dict) and "name" in item:
            names.append(item["name"])

    return " ".join(names)


def extract_year(release_date):
    """
    Extract the release year from a date string like '2009-12-10'.

    Storing the year helps OMDb find the correct movie later.
    Many movies share the same title, so the year improves search accuracy.

    Args:
        release_date: Date value from the CSV (may be missing).

    Returns:
        str: Four-digit year, or empty string if missing/invalid.
    """
    if pd.isna(release_date) or release_date == "":
        return ""

    try:
        # release_date format is usually YYYY-MM-DD, so year is the first part
        date_text = str(release_date).strip()
        year = date_text.split("-")[0]

        # Keep only valid 4-digit years
        if len(year) == 4 and year.isdigit():
            return year

        return ""
    except (IndexError, AttributeError):
        return ""


def extract_director(text):
    """
    Extract the Director's name from the crew column.

    Args:
        text (str): JSON-like crew string from the CSV.

    Returns:
        str: Director name, or empty string if not found.
    """
    if pd.isna(text) or text == "":
        return ""

    try:
        items = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return ""

    for item in items:
        if isinstance(item, dict):
            job = item.get("job", "")
            if job == "Director" and "name" in item:
                return item["name"]

    return ""


def clean_data(dataframe):
    """
    Keep required columns, remove bad rows, and convert text to strings.

    Rows with missing values are removed because the ML model needs
    complete text for every movie. Empty or NaN values would break
    similarity calculations later.

    Args:
        dataframe (pd.DataFrame): Merged dataset.

    Returns:
        pd.DataFrame: Cleaned dataset.
    """
    print("\nCleaning data...")

    # Keep only the columns we need
    cleaned_df = dataframe[REQUIRED_COLUMNS].copy()

    # Count rows before removing missing values
    rows_before = len(cleaned_df)

    # dropna removes any row that has at least one missing value
    cleaned_df = cleaned_df.dropna()

    rows_after = len(cleaned_df)
    removed_rows = rows_before - rows_after
    print(f"Removed {removed_rows} rows with missing values.")

    # Convert text columns to string type (id stays as a number)
    text_columns = [
        "title",
        "genres",
        "keywords",
        "overview",
        "cast",
        "crew",
        "release_date",
    ]
    for column_name in text_columns:
        cleaned_df[column_name] = cleaned_df[column_name].astype(str)

    print(f"Cleaned dataset has {len(cleaned_df)} rows.")
    return cleaned_df


def create_combined_features(dataframe):
    """
    Parse JSON-like columns and build one combined text feature per movie.

    Also converts text to lowercase and removes duplicate movie titles.

    Args:
        dataframe (pd.DataFrame): Cleaned dataset.

    Returns:
        pd.DataFrame: Dataset with a new 'combined_features' column.
    """
    print("\nCreating combined features...")

    processed_df = dataframe.copy()

    # Step 1: Extract release year safely from release_date
    # Year is saved separately because it helps OMDb find the correct movie
    processed_df["year"] = processed_df["release_date"].apply(extract_year)

    # Step 2: Convert JSON-like strings into plain readable text
    processed_df["genres"] = processed_df["genres"].apply(extract_names_from_json)
    processed_df["keywords"] = processed_df["keywords"].apply(
        extract_names_from_json
    )
    processed_df["cast"] = processed_df["cast"].apply(extract_cast_names)
    processed_df["crew"] = processed_df["crew"].apply(extract_director)

    # Step 3: Combine all text features into one column
    processed_df["combined_features"] = (
        processed_df["genres"]
        + " "
        + processed_df["keywords"]
        + " "
        + processed_df["overview"]
        + " "
        + processed_df["cast"]
        + " "
        + processed_df["crew"]
    )

    # Step 4: Lowercase helps match words like "Action" and "action"
    processed_df["combined_features"] = processed_df[
        "combined_features"
    ].str.lower()

    # Step 5: Remove duplicate titles (keep the first occurrence)
    duplicates_before = len(processed_df)
    processed_df = processed_df.drop_duplicates(subset=["title"], keep="first")
    duplicates_removed = duplicates_before - len(processed_df)

    print(f"Removed {duplicates_removed} duplicate movie titles.")
    print(f"Final dataset has {len(processed_df)} unique movies.")

    return processed_df


def save_processed_dataset(dataframe):
    """
    Save the processed dataset to a new CSV file.

    The original CSV files are NOT overwritten.

    Args:
        dataframe (pd.DataFrame): Final processed dataset.
    """
    print("\nSaving processed dataset...")

    # Keep only the columns needed for ML training and OMDb lookup
    final_df = dataframe[FINAL_COLUMNS].copy()

    # index=False means we do not save the row numbers as a column
    final_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved to: {OUTPUT_FILE}")


def main():
    """
    Run the full preprocessing pipeline from start to finish.
    """
    # Step 1: Load both CSV files
    movies_df, credits_df = load_datasets()

    # Step 2: Show information about each dataset
    display_dataset_info(movies_df, "Movies")
    display_dataset_info(credits_df, "Credits")

    # Step 3: Merge datasets on movie title
    merged_df = merge_datasets(movies_df, credits_df)

    # Step 5: Check required columns exist before processing
    validate_columns(merged_df)

    # Step 6 & 7: Clean missing values and convert to strings
    cleaned_df = clean_data(merged_df)

    # Step 8, 9 & 10: Build combined features, lowercase, remove duplicates
    processed_df = create_combined_features(cleaned_df)

    # Step 11: Save the result
    save_processed_dataset(processed_df)

    print("\nPreprocessing completed successfully.")


# Run main() only when this file is executed directly
if __name__ == "__main__":
    main()
