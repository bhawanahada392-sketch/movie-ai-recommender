from ai.ai_picks import build_fallback_ai_pick_titles, generate_ai_picks
from ai.chat_agent import build_fallback_answer


def test_chat_fallback_answer_for_horror():
    answer = build_fallback_answer("I want a horror movie")
    assert "horror" in answer.lower() or "scary" in answer.lower() or "The Others" in answer


def test_ai_picks_fallback_for_regional_query():
    titles = build_fallback_ai_pick_titles("hindi movie", [])
    assert len(titles) >= 3
    assert any("3 Idiots" in title for title in titles)


def test_generate_ai_picks_uses_fallback_when_gemini_empty(monkeypatch):
    monkeypatch.setattr("ai.ai_picks.call_gemini", lambda prompt: "")
    monkeypatch.setattr("ai.ai_picks.get_movie_details", lambda title, year: {"success": False})

    picks = generate_ai_picks("horror", [{"title": "The Shining", "year": "1980", "genre": "Horror", "plot": "A haunted hotel."}])

    assert len(picks) >= 3
