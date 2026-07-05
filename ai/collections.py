"""
collections.py - Curated collection helpers.

Collections use the existing processed dataset. No new dataset is added.
"""

from ml.recommender import format_year, movies_df


COLLECTION_KEYWORDS = {
    "weekend-movies": ["adventure", "action", "comedy"],
    "rainy-day": ["drama", "romance", "mystery"],
    "feel-good": ["comedy", "family", "friendship"],
    "mind-bending": ["mystery", "thriller", "science", "dream"],
    "family-night": ["family", "animation", "adventure"],
    "girls-night": ["romance", "comedy", "friendship"],
    "space-adventure": ["space", "alien", "science fiction"],
    "hidden-gems": ["independent", "drama", "story"],
}

COLLECTION_TITLES = {
    "weekend-movies": "Weekend Movies",
    "rainy-day": "Rainy Day",
    "feel-good": "Feel Good",
    "mind-bending": "Mind Bending",
    "family-night": "Family Night",
    "girls-night": "Girls Night",
    "space-adventure": "Space Adventure",
    "hidden-gems": "Hidden Gems",
}


def list_collections():
    """
    Return available collection names.

    Returns:
        list: Collection labels and slugs.
    """
    return [
        {
            "slug": slug,
            "title": COLLECTION_TITLES[slug],
        }
        for slug in COLLECTION_KEYWORDS
    ]


def movie_matches_keywords(row, keywords):
    """
    Check whether a dataset row matches collection keywords.

    Args:
        row: Dataset row.
        keywords (list): Words to search for.

    Returns:
        bool: True when at least one keyword matches.
    """
    combined_features = str(row.get("combined_features", "")).lower()
    title = str(row.get("title", "")).lower()

    for keyword in keywords:
        if keyword in combined_features or keyword in title:
            return True

    return False


def get_collection_movies(slug, limit=12):
    """
    Build a simple curated movie collection.

    Args:
        slug (str): Collection slug.
        limit (int): Maximum number of movies to return.

    Returns:
        dict: Collection data.
    """
    keywords = COLLECTION_KEYWORDS.get(slug)

    if not keywords or movies_df is None:
        return {
            "success": False,
            "message": "Collection not found.",
            "movies": [],
        }

    movies = []

    for index, row in movies_df.iterrows():
        if movie_matches_keywords(row, keywords):
            movies.append(
                {
                    "id": int(row["id"]),
                    "title": row["title"],
                    "year": format_year(row.get("year", "")),
                }
            )

        if len(movies) == limit:
            break

    return {
        "success": True,
        "slug": slug,
        "title": COLLECTION_TITLES[slug],
        "movies": movies,
    }
