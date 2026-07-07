from ai.chat_agent import build_fallback_answer


def test_chat_fallback_answer_for_horror():
    answer = build_fallback_answer("I want a horror movie")
    assert "horror" in answer.lower() or "scary" in answer.lower() or "The Others" in answer


def test_ai_picks_backend_list_removed():
    import app as app_module

    app_module.get_movie_details = lambda title, year=None: {
        "success": False,
        "message": "offline",
    }
    app_module.generate_overview_explanation = lambda searched, recs: "Explanation only."
    app_module.rerank_indian_recommendations = lambda recs, title: recs

    client = app_module.app.test_client()
    data = client.post("/recommend", json={"movie": "Avatar"}).get_json()

    assert data["success"]
    assert data["recommendations"]
    assert "ai_explanation" in data
    assert "ai_picks" not in data
