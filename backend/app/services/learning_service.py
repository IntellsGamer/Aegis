"""Learning center services."""
from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidationError
from app.models import User
from app.repositories.learning_repo import LearningRepository
from app.security.jwt import generate_random_token


def list_lessons(db: Session) -> list:
    repo = LearningRepository(db)
    lessons = repo.list_lessons()
    return lessons


def get_lesson(db: Session, slug: str) -> dict:
    repo = LearningRepository(db)
    lesson = repo.get_lesson(slug)
    if not lesson:
        raise NotFoundError("Lesson not found")
    return {"lesson": lesson}


def update_progress(db: Session, user: User, lesson_slug: str, progress: float,
                    completed: bool) -> dict:
    repo = LearningRepository(db)
    lesson = repo.get_lesson(lesson_slug)
    if not lesson:
        raise NotFoundError("Lesson not found")
    row = repo.upsert_progress(user.id, lesson.id, progress, completed)
    return {
        "lesson_slug": lesson_slug,
        "progress": row.progress,
        "completed": row.completed,
    }


def list_quizzes(db: Session) -> list:
    return LearningRepository(db).list_quizzes()


def get_quiz_detail(db: Session, slug: str, user: User | None) -> dict:
    repo = LearningRepository(db)
    quiz = repo.get_quiz(slug, with_questions=True)
    if not quiz:
        raise NotFoundError("Quiz not found")
    questions = sorted(quiz.questions, key=lambda q: q.order)
    payload = {
        "id": quiz.id,
        "slug": quiz.slug,
        "title": quiz.title,
        "category": quiz.category,
        "description": quiz.description,
        "pass_percent": quiz.pass_percent,
        "questions": [{
            "id": q.id, "text": q.text, "options": q.options,
            "explanation": q.explanation, "order": q.order,
        } for q in questions],
    }
    if user:
        best = repo.best_attempt(user.id, quiz.id)
        payload["best_score"] = best.score_percent if best else None
        payload["best_passed"] = best.passed if best else False
    return payload


def submit_quiz(db: Session, user: User, slug: str, answers: list[int]) -> dict:
    repo = LearningRepository(db)
    quiz = repo.get_quiz(slug, with_questions=True)
    if not quiz:
        raise NotFoundError("Quiz not found")
    questions = sorted(quiz.questions, key=lambda q: q.order)
    if len(answers) != len(questions):
        raise ValidationError(f"Expected {len(questions)} answers, got {len(answers)}")

    correct = 0
    explanations = []
    for idx, (answer, question) in enumerate(zip(answers, questions)):
        is_correct = answer == question.correct_index
        if is_correct:
            correct += 1
        explanations.append({
            "question": question.text,
            "your_answer": question.options[answer] if answer < len(question.options) else "?",
            "correct_answer": question.options[question.correct_index],
            "correct": is_correct,
            "explanation": question.explanation,
        })

    score_percent = round(correct / len(questions) * 100, 1)
    passed = score_percent >= quiz.pass_percent
    attempt = repo.create_attempt(user.id, quiz.id, score_percent, correct,
                                  len(questions), passed, answers)

    certificate_code = None
    if passed:
        cert = repo.certificate_for(user.id, quiz.id)
        if not cert:
            cert = repo.create_certificate(
                user.id, quiz.id, code=f"AEGIS-{generate_random_token(6)}"
            )
        certificate_code = cert.code

    return {
        "score_percent": score_percent,
        "correct_count": correct,
        "total_count": len(questions),
        "passed": passed,
        "certificate_code": certificate_code,
        "explanations": explanations,
        "attempt_id": attempt.id,
    }


def list_scenarios(db: Session) -> list:
    return LearningRepository(db).list_scenarios()


def answer_scenario(db: Session, user: User | None, scenario_id: int,
                    chosen_index: int) -> dict:
    repo = LearningRepository(db)
    scenario = repo.get_scenario(scenario_id)
    if not scenario:
        raise NotFoundError("Scenario not found")
    if chosen_index >= len(scenario.options):
        raise ValidationError("Invalid answer")

    correct = chosen_index == scenario.correct_index
    streak = 0
    if user:
        previous = repo.streak(user.id)
        streak = previous + 1 if correct else 0
        repo.record_attempt(user.id, scenario_id, chosen_index, correct, streak)
    else:
        repo.record_attempt(None, scenario_id, chosen_index, correct, 0)

    return {
        "correct": correct,
        "correct_index": scenario.correct_index,
        "explanation": scenario.explanation,
        "red_flags": scenario.red_flags,
        "streak": streak,
    }


def progress(db: Session, user: User) -> dict:
    repo = LearningRepository(db)
    lessons_total = repo.lessons_total()
    lessons_completed = repo.lessons_completed(user.id)
    quizzes_total = repo.quizzes_total()
    quizzes_passed = repo.quizzes_passed(user.id)
    points = repo.points(user.id)
    streak = repo.streak(user.id)

    level = "Novice"
    if points >= 500:
        level = "Security Guardian"
    elif points >= 250:
        level = "Security Sentinel"
    elif points >= 100:
        level = "Security Apprentice"

    return {
        "lessons_completed": lessons_completed,
        "lessons_total": lessons_total,
        "quizzes_passed": quizzes_passed,
        "quizzes_total": quizzes_total,
        "streak": streak,
        "points": points,
        "level": level,
        "certificates": [{"code": c.code, "quiz_id": c.quiz_id, "awarded_at": c.awarded_at}
                         for c in repo.user_certificates(user.id)],
    }
