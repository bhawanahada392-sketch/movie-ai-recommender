"""
preprocess.py - Build one clean recommendation dataset.

This script merges the original TMDB 5000 data with the Bollywood CSV.
It keeps the project beginner-friendly by using pandas, simple helper
functions, TF-IDF-ready text tags, and safe missing-value handling.
"""

import ast
import os
import re
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

TMDB_MOVIES_FILE = os.path.join(DATA_DIR, "tmdb_5000_movies.csv")
TMDB_CREDITS_FILE = os.path.join(DATA_DIR, "tmdb_5000_credits.csv")
BOLLYWOOD_FILE = os.path.join(DATA_DIR, "bollywood_movies.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "processed_movies.csv")
TEMP_OUTPUT_FILE = os.path.join(DATA_DIR, "processed_movies_new.csv")

FINAL_COLUMNS = [
    "id",
    "title",
    "year",
    "language",
    "genres",
    "overview",
    "keywords",
    "cast",
    "director",
    "poster",
    "rating",
    "combined_features",
    "tags",
    "source",
]

CURATED_INDIAN_MOVIES = [
    {
        "id": 256040,
        "title": "Baahubali: The Beginning",
        "year": "2015",
        "language": "telugu",
        "genres": "action adventure drama fantasy",
        "overview": "A young man discovers his royal past and rises into a large-scale battle for justice and identity.",
        "keywords": "indian cinema kingdom warrior revenge epic palace battle",
        "cast": "Prabhas Rana Daggubati Tamannaah Bhatia Anushka Shetty Ramya Krishnan",
        "director": "S. S. Rajamouli",
        "poster": "",
        "rating": "7.5",
        "source": "curated",
    },
    {
        "id": 350312,
        "title": "Baahubali 2: The Conclusion",
        "year": "2017",
        "language": "telugu",
        "genres": "action adventure drama fantasy",
        "overview": "A heroic prince's legacy fuels a sweeping fight for a kingdom, family honor, and justice.",
        "keywords": "indian cinema kingdom warrior revenge epic palace battle sequel",
        "cast": "Prabhas Rana Daggubati Anushka Shetty Tamannaah Bhatia Sathyaraj",
        "director": "S. S. Rajamouli",
        "poster": "",
        "rating": "7.4",
        "source": "curated",
    },
    {
        "id": 579974,
        "title": "RRR",
        "year": "2022",
        "language": "telugu",
        "genres": "action drama",
        "overview": "Two legendary revolutionaries form a friendship and fight against colonial rule in India.",
        "keywords": "indian cinema revolution friendship british empire patriotic epic",
        "cast": "N. T. Rama Rao Jr. Ram Charan Alia Bhatt Ajay Devgn",
        "director": "S. S. Rajamouli",
        "poster": "",
        "rating": "7.8",
        "source": "curated",
    },
    {
        "id": 496331,
        "title": "Jawan",
        "year": "2023",
        "language": "hindi",
        "genres": "action thriller drama",
        "overview": "A driven vigilante challenges corruption while confronting family secrets and a dangerous enemy.",
        "keywords": "bollywood indian cinema vigilante revenge corruption father son action",
        "cast": "Shah Rukh Khan Nayanthara Vijay Sethupathi Deepika Padukone",
        "director": "Atlee",
        "poster": "",
        "rating": "7.0",
        "source": "curated",
    },
    {
        "id": 19666,
        "title": "Lagaan",
        "year": "2001",
        "language": "hindi",
        "genres": "drama sport musical",
        "overview": "Villagers under colonial pressure challenge their rulers to a cricket match that could change their future.",
        "keywords": "bollywood indian cinema cricket village colonial underdog inspirational",
        "cast": "Aamir Khan Gracy Singh Rachel Shelley Paul Blackthorne",
        "director": "Ashutosh Gowariker",
        "poster": "",
        "rating": "7.3",
        "source": "curated",
    },
    {
        "id": 7913,
        "title": "Rang De Basanti",
        "year": "2006",
        "language": "hindi",
        "genres": "drama history comedy",
        "overview": "Friends making a film about revolutionaries awaken to social injustice in their own time.",
        "keywords": "bollywood indian cinema friendship youth revolution patriotic political",
        "cast": "Aamir Khan Siddharth Sharman Joshi Kunal Kapoor Soha Ali Khan",
        "director": "Rakeysh Omprakash Mehra",
        "poster": "",
        "rating": "7.2",
        "source": "curated",
    },
    {
        "id": 7508,
        "title": "Like Stars on Earth",
        "year": "2007",
        "language": "hindi",
        "genres": "drama family",
        "overview": "A sensitive teacher helps a misunderstood child rediscover confidence, creativity, and joy in learning.",
        "keywords": "bollywood indian cinema school education child teacher emotional inspirational",
        "cast": "Darsheel Safary Aamir Khan Tisca Chopra",
        "director": "Aamir Khan",
        "poster": "",
        "rating": "8.3",
        "source": "curated",
    },
    {
        "id": 26022,
        "title": "My Name Is Khan",
        "year": "2010",
        "language": "hindi",
        "genres": "drama romance",
        "overview": "A kind man crosses America to repair a broken life and challenge prejudice after a family tragedy.",
        "keywords": "bollywood indian cinema family prejudice journey emotional love",
        "cast": "Shah Rukh Khan Kajol Jimmy Shergill",
        "director": "Karan Johar",
        "poster": "",
        "rating": "8.0",
        "source": "curated",
    },
    {
        "id": 19675,
        "title": "Swades",
        "year": "2004",
        "language": "hindi",
        "genres": "drama family",
        "overview": "An Indian scientist working abroad returns home and reconnects with a village that changes his priorities.",
        "keywords": "bollywood indian cinema village homecoming social change inspirational",
        "cast": "Shah Rukh Khan Gayatri Joshi Kishori Ballal",
        "director": "Ashutosh Gowariker",
        "poster": "",
        "rating": "7.3",
        "source": "curated",
    },
    {
        "id": 20496,
        "title": "Munna Bhai M.B.B.S.",
        "year": "2003",
        "language": "hindi",
        "genres": "comedy drama",
        "overview": "A kind-hearted gangster enters medical college and changes people with humor, empathy, and warmth.",
        "keywords": "bollywood indian cinema medical college friendship comedy feel good",
        "cast": "Sanjay Dutt Arshad Warsi Gracy Singh Boman Irani",
        "director": "Rajkumar Hirani",
        "poster": "",
        "rating": "7.2",
        "source": "curated",
    },
    {
        "id": 15917,
        "title": "Hum Aapke Hain Koun..!",
        "year": "1994",
        "language": "hindi",
        "genres": "romance drama family musical",
        "overview": "Two families celebrate love, music, and tradition while a young couple faces an emotional choice.",
        "keywords": "bollywood indian cinema family wedding romance musical tradition",
        "cast": "Salman Khan Madhuri Dixit Mohnish Bahl Renuka Shahane",
        "director": "Sooraj R. Barjatya",
        "poster": "",
        "rating": "6.3",
        "source": "curated",
    },
    {
        "id": 14072,
        "title": "Hum Dil De Chuke Sanam",
        "year": "1999",
        "language": "hindi",
        "genres": "romance drama musical",
        "overview": "A newly married man helps his wife search for the musician she once loved.",
        "keywords": "bollywood indian cinema love marriage music sacrifice emotional",
        "cast": "Salman Khan Aishwarya Rai Bachchan Ajay Devgn",
        "director": "Sanjay Leela Bhansali",
        "poster": "",
        "rating": "6.4",
        "source": "curated",
    },
    {
        "id": 14756,
        "title": "Tere Naam",
        "year": "2003",
        "language": "hindi",
        "genres": "romance drama action",
        "overview": "A troubled young man changes through love, but fate pulls his life into tragedy.",
        "keywords": "bollywood indian cinema love tragedy college emotional",
        "cast": "Salman Khan Bhumika Chawla Sachin Khedekar",
        "director": "Satish Kaushik",
        "poster": "",
        "rating": "6.5",
        "source": "curated",
    },
    {
        "id": 16562,
        "title": "Bajrangi Bhaijaan",
        "year": "2015",
        "language": "hindi",
        "genres": "comedy drama action adventure",
        "overview": "A kind-hearted man helps a lost child return home across the border.",
        "keywords": "bollywood indian cinema child journey border kindness emotional",
        "cast": "Salman Khan Harshaali Malhotra Kareena Kapoor Nawazuddin Siddiqui",
        "director": "Kabir Khan",
        "poster": "",
        "rating": "7.8",
        "source": "curated",
    },
    {
        "id": 19622,
        "title": "Sultan",
        "year": "2016",
        "language": "hindi",
        "genres": "drama action sport romance",
        "overview": "A wrestler fights to rebuild his career, marriage, and self-respect.",
        "keywords": "bollywood indian cinema wrestling sports comeback inspirational",
        "cast": "Salman Khan Anushka Sharma Randeep Hooda Amit Sadh",
        "director": "Ali Abbas Zafar",
        "poster": "",
        "rating": "7.0",
        "source": "curated",
    },
    {
        "id": 20115,
        "title": "Ek Tha Tiger",
        "year": "2012",
        "language": "hindi",
        "genres": "action thriller romance",
        "overview": "An Indian spy falls in love while working on a dangerous international mission.",
        "keywords": "bollywood indian cinema spy action mission romance espionage",
        "cast": "Salman Khan Katrina Kaif Ranvir Shorey Girish Karnad",
        "director": "Kabir Khan",
        "poster": "",
        "rating": "6.5",
        "source": "curated",
    },
    {
        "id": 564147,
        "title": "K.G.F: Chapter 1",
        "year": "2018",
        "language": "kannada",
        "genres": "action crime drama",
        "overview": "A determined man rises through a violent gold-mining underworld.",
        "keywords": "indian cinema gangster gold mine power revenge",
        "cast": "Yash Srinidhi Shetty Ramachandra Raju",
        "director": "Prashanth Neel",
        "poster": "",
        "rating": "8.2",
        "source": "curated",
    },
    {
        "id": 587412,
        "title": "K.G.F: Chapter 2",
        "year": "2022",
        "language": "kannada",
        "genres": "action crime drama",
        "overview": "Rocky defends his empire while powerful enemies close in around him.",
        "keywords": "indian cinema gangster gold mine power revenge sequel",
        "cast": "Yash Sanjay Dutt Srinidhi Shetty Raveena Tandon",
        "director": "Prashanth Neel",
        "poster": "",
        "rating": "8.3",
        "source": "curated",
    },
    {
        "id": 20453,
        "title": "3 Idiots",
        "year": "2009",
        "language": "hindi",
        "genres": "comedy drama",
        "overview": "Three engineering students challenge a rigid education system and search for their true passions.",
        "keywords": "indian cinema college friendship education feel good",
        "cast": "Aamir Khan R. Madhavan Sharman Joshi Kareena Kapoor",
        "director": "Rajkumar Hirani",
        "poster": "",
        "rating": "8.0",
        "source": "curated",
    },
    {
        "id": 360814,
        "title": "Dangal",
        "year": "2016",
        "language": "hindi",
        "genres": "drama action family",
        "overview": "A former wrestler trains his daughters to become world-class champions.",
        "keywords": "indian cinema wrestling sports family inspirational",
        "cast": "Aamir Khan Fatima Sana Shaikh Sanya Malhotra Sakshi Tanwar",
        "director": "Nitesh Tiwari",
        "poster": "",
        "rating": "7.9",
        "source": "curated",
    },
]


def display_dataset_info(dataframe, dataset_name):
    """Print simple dataset details for inspection."""
    print(f"\n--- {dataset_name} Dataset Info ---")
    print(f"Rows: {len(dataframe)}")
    print(f"Columns: {list(dataframe.columns)}")
    print("Datatypes:")
    print(dataframe.dtypes.astype(str).to_string())


def load_datasets():
    """Load every raw CSV used by the recommender."""
    print("Loading datasets...")
    tmdb_movies = pd.read_csv(TMDB_MOVIES_FILE)
    tmdb_credits = pd.read_csv(TMDB_CREDITS_FILE)
    bollywood_movies = pd.read_csv(BOLLYWOOD_FILE)

    display_dataset_info(tmdb_movies, "TMDB Movies")
    display_dataset_info(tmdb_credits, "TMDB Credits")
    display_dataset_info(bollywood_movies, "Bollywood Movies")

    print("\nCommon columns:")
    print(
        sorted(
            set(tmdb_movies.columns)
            .intersection(tmdb_credits.columns)
            .intersection(bollywood_movies.columns)
        )
    )

    return tmdb_movies, tmdb_credits, bollywood_movies


def safe_text(value):
    """Return clean text for missing, numeric, or normal string values."""
    if pd.isna(value):
        return ""
    return str(value).strip()


def parse_json_list(value):
    """Safely parse TMDB JSON-like list columns."""
    text = safe_text(value)
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return []

    if isinstance(parsed, list):
        return parsed

    return []


def extract_names_from_json(value):
    """Extract name fields from TMDB genres/keywords JSON."""
    names = []
    for item in parse_json_list(value):
        if isinstance(item, dict) and item.get("name"):
            names.append(safe_text(item["name"]))
    return " ".join(names)


def extract_cast_names(value, max_actors=12):
    """Extract the first few actor names from TMDB cast JSON."""
    names = []
    for item in parse_json_list(value)[:max_actors]:
        if isinstance(item, dict) and item.get("name"):
            names.append(safe_text(item["name"]))
    return " ".join(names)


def extract_director(value):
    """Extract the director from TMDB crew JSON."""
    for item in parse_json_list(value):
        if isinstance(item, dict) and item.get("job") == "Director":
            return safe_text(item.get("name", ""))
    return ""


def extract_year(value):
    """Convert dates or numeric year values into a clean four-digit year."""
    text = safe_text(value)
    if not text:
        return ""

    match = re.search(r"\d{4}", text)
    if match:
        return match.group(0)

    return ""


def normalize_language(value):
    """Normalize language codes into simple lowercase text."""
    text = safe_text(value).lower()
    language_map = {
        "en": "english",
        "hi": "hindi",
        "ta": "tamil",
        "te": "telugu",
        "ml": "malayalam",
        "kn": "kannada",
    }
    return language_map.get(text, text)


def normalize_words(value):
    """Lowercase text and keep readable spacing for TF-IDF/search."""
    text = safe_text(value).lower()
    text = re.sub(r"[\[\]{}\"|,/;]+", " ", text)
    text = re.sub(r"[^a-z0-9&.:\-'\s]", " ", text)
    return " ".join(text.split())


def normalize_people_text(value):
    """Normalize actor/director style fields from CSV, pipes, or list text."""
    text = safe_text(value)
    parsed_names = []

    for item in parse_json_list(text):
        if isinstance(item, dict) and item.get("name"):
            parsed_names.append(safe_text(item["name"]))
        elif isinstance(item, str):
            parsed_names.append(safe_text(item))

    if parsed_names:
        text = " ".join(parsed_names)

    return normalize_words(text)


def title_key(title):
    """Create a duplicate-friendly title key."""
    text = normalize_words(title)
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def standardize_tmdb(tmdb_movies, tmdb_credits):
    """Convert TMDB movies + credits into the shared schema."""
    print("\nStandardizing TMDB dataset...")
    merged = tmdb_movies.merge(tmdb_credits, on="title", how="left")

    rows = pd.DataFrame()
    rows["id"] = merged["id"]
    rows["title"] = merged["title"].apply(safe_text)
    rows["year"] = merged["release_date"].apply(extract_year)
    rows["language"] = merged["original_language"].apply(normalize_language)
    rows["genres"] = merged["genres"].apply(extract_names_from_json)
    rows["overview"] = merged["overview"].apply(safe_text)
    rows["keywords"] = merged["keywords"].apply(extract_names_from_json)
    rows["cast"] = merged["cast"].apply(extract_cast_names)
    rows["director"] = merged["crew"].apply(extract_director)
    rows["poster"] = ""
    rows["rating"] = merged.get("vote_average", "")
    rows["source"] = "tmdb"

    print(f"TMDB standardized rows: {len(rows)}")
    return rows


def standardize_bollywood(bollywood_movies):
    """Convert the Bollywood CSV into the shared schema."""
    print("\nStandardizing Bollywood dataset...")
    rows = pd.DataFrame()
    rows["id"] = bollywood_movies["id"]
    rows["title"] = bollywood_movies["title"].apply(safe_text)
    rows["year"] = bollywood_movies.get("year", pd.Series([""] * len(bollywood_movies))).apply(extract_year)
    rows["language"] = "hindi"
    rows["genres"] = ""
    rows["overview"] = ""
    rows["keywords"] = "bollywood indian cinema hindi"
    rows["cast"] = ""
    rows["director"] = ""
    rows["poster"] = ""
    rows["rating"] = bollywood_movies.get("rating", "")
    rows["source"] = "bollywood"

    print(f"Bollywood standardized rows: {len(rows)}")
    return rows


def load_curated_indian_movies():
    """
    Add a tiny metadata safety net for famous Indian movies that are missing
    or too sparse in the provided Bollywood CSV.
    """
    print("\nLoading curated Indian metadata rows...")
    rows = pd.DataFrame(CURATED_INDIAN_MOVIES)
    print(f"Curated rows: {len(rows)}")
    return rows


def metadata_quality_score(row):
    """Score rows so duplicate removal keeps the most useful record."""
    score = 0

    if safe_text(row.get("poster")):
        score += 20
    if safe_text(row.get("overview")):
        score += 12
    if safe_text(row.get("genres")):
        score += 10
    if safe_text(row.get("cast")):
        score += 8
    if safe_text(row.get("director")):
        score += 8
    if safe_text(row.get("keywords")):
        score += 5
    if safe_text(row.get("year")):
        score += 3

    try:
        rating = float(row.get("rating", 0) or 0)
    except (TypeError, ValueError):
        rating = 0
    score += min(rating, 10) / 10

    return score


def first_useful_value(rows, column):
    """Pick the highest-quality non-empty value for one metadata column."""
    values = []

    for _, row in rows.iterrows():
        value = safe_text(row.get(column, ""))
        if value:
            values.append((metadata_quality_score(row), value))

    if not values:
        return ""

    values.sort(key=lambda item: -item[0])
    return values[0][1]


def fill_missing_duplicate_metadata(dataframe):
    """
    Fill missing metadata between duplicate IDs/titles before dropping copies.
    """
    print("\nFilling metadata from duplicate rows...")
    working = dataframe.copy()
    fill_columns = [
        "genres",
        "overview",
        "keywords",
        "cast",
        "director",
        "poster",
        "rating",
        "language",
        "year",
    ]

    working["title_key"] = working["title"].apply(title_key)
    filled_count = 0

    for _, group in working.groupby("title_key", sort=False):
        if len(group) < 2:
            continue

        for column in fill_columns:
            best_value = first_useful_value(group, column)

            if not best_value:
                continue

            empty_mask = group[column].fillna("").astype(str).str.strip() == ""
            if empty_mask.any():
                working.loc[group[empty_mask].index, column] = best_value
                filled_count += int(empty_mask.sum())

    working = working.drop(columns=["title_key"])
    print(f"Filled {filled_count} missing duplicate metadata values.")
    return working


def remove_duplicates(dataframe):
    """Remove duplicate IDs and duplicate titles while keeping best rows."""
    print("\nRemoving duplicates...")
    before = len(dataframe)
    working = fill_missing_duplicate_metadata(dataframe)
    working["quality_score"] = working.apply(metadata_quality_score, axis=1)

    working = working.sort_values(
        by=["quality_score", "source"],
        ascending=[False, True],
    )
    working = working.drop_duplicates(subset=["id"], keep="first")
    after_id = len(working)

    working["title_key"] = working["title"].apply(title_key)
    working = working.drop_duplicates(subset=["title_key"], keep="first")
    after_title = len(working)

    working = working.drop(columns=["quality_score", "title_key"])
    working = working.sort_values(by=["title"]).reset_index(drop=True)

    print(f"Removed {before - after_id} duplicate IDs.")
    print(f"Removed {after_id - after_title} duplicate titles.")
    print(f"Rows after duplicates: {len(working)}")
    return working


def clean_data(dataframe):
    """Handle missing values and remove rows with too little information."""
    print("\nCleaning merged data...")
    cleaned = dataframe.copy()

    for column in FINAL_COLUMNS:
        if column not in cleaned.columns:
            cleaned[column] = ""

    cleaned["title"] = cleaned["title"].apply(safe_text)
    cleaned = cleaned[cleaned["title"] != ""]

    for column in [
        "language",
        "genres",
        "overview",
        "keywords",
        "cast",
        "director",
        "poster",
        "source",
    ]:
        if column in ["cast", "director"]:
            cleaned[column] = cleaned[column].apply(normalize_people_text)
        else:
            cleaned[column] = cleaned[column].apply(normalize_words)

    cleaned["year"] = cleaned["year"].apply(extract_year)
    cleaned["rating"] = cleaned["rating"].apply(safe_text)

    print("Kept all titled rows; sparse metadata is filled with safe blanks.")
    print(f"Cleaned rows: {len(cleaned)}")
    return cleaned


def create_tags(dataframe):
    """Create the text feature used by TF-IDF and cosine similarity."""
    print("\nCreating recommendation tags...")
    processed = dataframe.copy()

    processed["tags"] = (
        (
            processed["overview"].fillna("")
            + " "
            + processed["genres"].fillna("") + " " + processed["genres"].fillna("")
            + " "
            + processed["keywords"].fillna("") + " " + processed["keywords"].fillna("")
            + " "
            + processed["cast"].fillna("") + " " + processed["cast"].fillna("")
            + " "
            + processed["director"].fillna("") + " " + processed["director"].fillna("")
        ).apply(normalize_words)
    )

    # Keep the old column name so the existing model code stays familiar.
    processed["combined_features"] = processed["tags"]

    return processed


def validate_processed_dataset(dataframe):
    """Check that the new processed file is safe before replacing the old one."""
    missing = [column for column in FINAL_COLUMNS if column not in dataframe.columns]
    if missing:
        print("\nERROR: Missing final columns:")
        for column in missing:
            print(f"  - {column}")
        sys.exit(1)

    if len(dataframe) == 0:
        print("\nERROR: Processed dataset is empty.")
        sys.exit(1)

    if dataframe["combined_features"].fillna("").str.strip().eq("").any():
        print("\nERROR: Some rows have empty recommendation tags.")
        sys.exit(1)

    print("Processed dataset validation passed.")


def save_processed_dataset(dataframe):
    """Save to a temporary file first, then replace the active dataset."""
    print("\nSaving processed dataset...")
    final_df = dataframe[FINAL_COLUMNS].copy()
    final_df.to_csv(TEMP_OUTPUT_FILE, index=False)

    reloaded = pd.read_csv(TEMP_OUTPUT_FILE)
    validate_processed_dataset(reloaded)

    os.replace(TEMP_OUTPUT_FILE, OUTPUT_FILE)
    print(f"Saved verified dataset to: {OUTPUT_FILE}")


def main():
    """Run the full preprocessing pipeline."""
    tmdb_movies, tmdb_credits, bollywood_movies = load_datasets()

    tmdb_standard = standardize_tmdb(tmdb_movies, tmdb_credits)
    bollywood_standard = standardize_bollywood(bollywood_movies)

    curated_standard = load_curated_indian_movies()

    merged = pd.concat(
        [tmdb_standard, bollywood_standard, curated_standard],
        ignore_index=True,
    )
    print(f"\nMerged rows before cleaning: {len(merged)}")

    deduped = remove_duplicates(merged)
    cleaned = clean_data(deduped)
    processed = create_tags(cleaned)
    validate_processed_dataset(processed)
    save_processed_dataset(processed)

    print("\nPreprocessing completed successfully.")


if __name__ == "__main__":
    main()
