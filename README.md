# AI Movie Recommendation System

A beginner-friendly college project that recommends movies using Machine Learning, Flask, the TMDB API, and a simple Agentic AI workflow.

## Project Overview

This web application lets users search for a movie and receive personalized recommendations. The system learns patterns from movie data using scikit-learn, fetches live movie details from TMDB, and uses a simple AI agent to explain recommendations in plain language.

## Features (Planned)

- Search for movies by title
- Get ML-based movie recommendations
- Fetch movie posters and details from TMDB
- AI-powered explanation of why movies were recommended
- Clean, responsive web interface

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Main programming language |
| Flask | Web framework for the backend |
| pandas & numpy | Data handling for ML |
| scikit-learn | Machine learning model |
| requests | HTTP calls to TMDB API |
| python-dotenv | Load API keys from `.env` file |
| HTML, CSS, JavaScript | Frontend user interface |

## Folder Structure

```
movie-ai-recommender/
├── app.py                 # Flask app entry point
├── requirements.txt       # Python packages to install
├── README.md              # Project documentation
├── .env.example           # Example environment variables
├── .gitignore             # Files Git should ignore
├── data/                  # Movie dataset files
├── models/                # Saved ML model files (.pkl)
├── ml/                    # Machine learning code
├── api/                   # TMDB API integration
├── ai/                    # AI agent and LLM helpers
├── templates/             # HTML pages
└── static/                # CSS, JavaScript, images
```

## How to Install

1. **Clone or download** this project to your computer.

2. **Open a terminal** in the project folder:
   ```bash
   cd movie-ai-recommender
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

5. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set up your API key:**
   - Copy `.env.example` to `.env`
   - Replace `your_api_key_here` with your TMDB API key

## How to Run

1. Make sure your virtual environment is activated.

2. Start the Flask server:
   ```bash
   python app.py
   ```

3. Open your browser and go to:
   ```
   http://127.0.0.1:5000
   ```

4. You should see the project homepage.

## Screenshots

<!-- Add screenshots here after the project is complete -->

- **Homepage:** _(screenshot coming soon)_
- **Search results:** _(screenshot coming soon)_
- **Recommendations:** _(screenshot coming soon)_
