"""Learning center API blueprint."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.dependencies import db_session, login_required, optional_login
from app.exceptions import ValidationError
from app.services import learning_service

bp = Blueprint("learning_api", __name__, url_prefix="/api/v1/learning")


@bp.get("/lessons")
def lessons():
    items = learning_service.list_lessons(db_session())
    return jsonify([{
        "id": l.id, "slug": l.slug, "title": l.title, "category": l.category,
        "summary": l.summary, "content": l.content, "example": l.example,
        "tips": l.tips if isinstance(l.tips, list) else [], 
        "reading_time": l.reading_time, "order": l.order,
    } for l in items])

@bp.get("/lessons/<slug>")
def lesson(slug: str):
    lesson_data = learning_service.get_lesson(db_session(), slug)
    lesson = lesson_data["lesson"]
    # Serialize the underlying record; the service retains a wrapper for its
    # internal contract, but clients need the lesson's actual display fields.
    return jsonify({
        "id": lesson.id,
        "slug": lesson.slug,
        "title": lesson.title,
        "category": lesson.category,
        "summary": lesson.summary,
        "content": lesson.content,
        "example": lesson.example,
        "tips": lesson.tips if isinstance(lesson.tips, list) else [],
        "reading_time": lesson.reading_time,
        "order": lesson.order,
    })


@bp.post("/lessons/<slug>/progress")
@login_required
def lesson_progress(slug: str):
    from app.dependencies import current_user

    data = request.get_json(silent=True) or {}
    progress = float(data.get("progress", 0))
    completed = bool(data.get("completed", False))
    return jsonify(learning_service.update_progress(
        db_session(), current_user(), slug, progress, completed
    ))


@bp.get("/quizzes")
def quizzes():
    items = learning_service.list_quizzes(db_session())
    return jsonify([{
        "id": q.id, "slug": q.slug, "title": q.title, "category": q.category,
        "description": q.description, "pass_percent": q.pass_percent,
    } for q in items])


@bp.get("/quizzes/<slug>")
@optional_login
def quiz_detail(slug: str):
    from app.dependencies import current_user

    return jsonify(learning_service.get_quiz_detail(db_session(), slug, current_user()))


@bp.post("/quizzes/<slug>/submit")
@login_required
def quiz_submit(slug: str):
    from app.dependencies import current_user

    data = request.get_json(silent=True) or {}
    answers = data.get("answers")
    # Handle both list of integers and list of objects with index
    if not isinstance(answers, list):
        raise ValidationError("Answers must be a list")
    # Convert to integers if they're objects with an index property
    processed_answers = []
    for a in answers:
        if isinstance(a, int):
            processed_answers.append(a)
        elif isinstance(a, dict) and "index" in a:
            processed_answers.append(a["index"])
        elif isinstance(a, (str, float)) and str(a).isdigit():
            processed_answers.append(int(a))
        else:
            raise ValidationError("Each answer must be an integer or object with 'index'")
    if not all(isinstance(a, int) for a in processed_answers):
        raise ValidationError("Answers must be convertible to integers")
    return jsonify(learning_service.submit_quiz(db_session(), current_user(), slug, processed_answers))


@bp.get("/simulator")
def scenarios():
    items = learning_service.list_scenarios(db_session())
    return jsonify([{
        "id": s.id, "slug": s.slug, "title": s.title, "category": s.category,
        "difficulty": s.difficulty, "content": s.content, "options": s.options,
    } for s in items])


@bp.post("/simulator/answer")
@optional_login
def answer_scenario():
    from app.dependencies import current_user

    data = request.get_json(silent=True) or {}
    scenario_id = data.get("scenario_id")
    chosen = data.get("chosen_index")
    if not isinstance(scenario_id, int) or not isinstance(chosen, int):
        raise ValidationError("scenario_id and chosen_index are required")
    return jsonify(learning_service.answer_scenario(
        db_session(), current_user(), scenario_id, chosen
    ))


@bp.get("/progress")
@login_required
def progress():
    from app.dependencies import current_user

    return jsonify(learning_service.progress(db_session(), current_user()))
