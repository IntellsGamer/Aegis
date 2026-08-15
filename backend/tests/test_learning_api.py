"""Learning API contracts for lessons and quizzes shown by the Turbo client."""


def test_lesson_detail_serializes_the_underlying_lesson(client):
    response = client.get("/api/v1/learning/lessons/what-is-phishing")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["slug"] == "what-is-phishing"
    assert payload["title"] == "What is Phishing?"
    assert payload["content"]
    assert payload["example"]
    assert len(payload["tips"]) >= 3


def test_learning_center_exposes_quizzes_with_questions(client):
    listing = client.get("/api/v1/learning/quizzes")
    assert listing.status_code == 200
    quizzes = listing.get_json()
    assert any(item["slug"] == "phishing-101" for item in quizzes)

    detail = client.get("/api/v1/learning/quizzes/phishing-101")
    assert detail.status_code == 200
    payload = detail.get_json()
    assert payload["title"] == "Phishing 101"
    assert len(payload["questions"]) == 4
    assert all(question["options"] for question in payload["questions"])
