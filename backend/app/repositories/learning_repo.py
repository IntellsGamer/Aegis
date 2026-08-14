"""Learning repository: lessons, quizzes, certificates, simulator."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Certificate,
    Lesson,
    LessonProgress,
    Quiz,
    QuizAttempt,
    QuizQuestion,
    SimulatorAttempt,
    SimulatorScenario,
    User,
)
from app.utils.time import utcnow


class LearningRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- lessons ----------------------------------------------------------
    def list_lessons(self):
        return self.db.scalars(
            select(Lesson).where(Lesson.published.is_(True)).order_by(Lesson.order)
        ).all()

    def get_lesson(self, slug: str) -> Lesson | None:
        return self.db.scalar(select(Lesson).where(Lesson.slug == slug))

    def progress(self, user_id: int, lesson_id: int) -> LessonProgress | None:
        return self.db.scalar(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
            )
        )

    def upsert_progress(self, user_id: int, lesson_id: int, progress: float,
                        completed: bool) -> LessonProgress:
        row = self.progress(user_id, lesson_id)
        if row is None:
            row = LessonProgress(user_id=user_id, lesson_id=lesson_id)
        row.progress = progress
        if completed:
            row.completed = True
            row.completed_at = row.completed_at or utcnow()
        self.db.add(row)
        self.db.flush()
        return row

    # --- quizzes ----------------------------------------------------------
    def list_quizzes(self):
        return self.db.scalars(select(Quiz).where(Quiz.published.is_(True))).all()

    def get_quiz(self, slug: str, with_questions: bool = True) -> Quiz | None:
        stmt = select(Quiz).where(Quiz.slug == slug)
        if with_questions:
            stmt = stmt.options(selectinload(Quiz.questions))
        return self.db.scalar(stmt)

    def best_attempt(self, user_id: int, quiz_id: int) -> QuizAttempt | None:
        return self.db.scalar(
            select(QuizAttempt)
            .where(QuizAttempt.user_id == user_id, QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.score_percent.desc())
        )

    def create_attempt(self, user_id: int, quiz_id: int, score: float,
                       correct: int, total: int, passed: bool, answers: list | None) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id, quiz_id=quiz_id, score_percent=score,
            correct_count=correct, total_count=total, passed=passed, answers=answers or [],
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def certificate_for(self, user_id: int, quiz_id: int) -> Certificate | None:
        return self.db.scalar(
            select(Certificate).where(Certificate.user_id == user_id, Certificate.quiz_id == quiz_id)
        )

    def create_certificate(self, user_id: int, quiz_id: int, code: str) -> Certificate:
        cert = Certificate(user_id=user_id, quiz_id=quiz_id, code=code)
        self.db.add(cert)
        self.db.flush()
        return cert

    def user_certificates(self, user_id: int) -> list[Certificate]:
        return self.db.scalars(
            select(Certificate).where(Certificate.user_id == user_id).order_by(Certificate.awarded_at.desc())
        ).all()

    # --- simulator ----------------------------------------------------------
    def list_scenarios(self):
        return self.db.scalars(
            select(SimulatorScenario).where(SimulatorScenario.published.is_(True))
        ).all()

    def get_scenario(self, scenario_id: int) -> SimulatorScenario | None:
        return self.db.get(SimulatorScenario, scenario_id)

    def record_attempt(self, user_id: int | None, scenario_id: int, chosen: int,
                       correct: bool, streak: int) -> SimulatorAttempt:
        attempt = SimulatorAttempt(
            user_id=user_id, scenario_id=scenario_id, chosen_index=chosen,
            correct=correct, streak=streak,
        )
        self.db.add(attempt)
        self.db.flush()
        return attempt

    def streak(self, user_id: int) -> int:
        last = self.db.scalar(
            select(SimulatorAttempt)
            .where(SimulatorAttempt.user_id == user_id)
            .order_by(SimulatorAttempt.id.desc())
        )
        if not last:
            return 0
        if last.correct:
            return last.streak
        return 0

    # --- progress / stats -----------------------------------------------------
    def lessons_total(self) -> int:
        return self.db.scalar(select(func.count(Lesson.id)).where(Lesson.published.is_(True))) or 0

    def lessons_completed(self, user_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(LessonProgress.id)).where(
                    LessonProgress.user_id == user_id, LessonProgress.completed.is_(True)
                )
            ) or 0
        )

    def quizzes_total(self) -> int:
        return self.db.scalar(select(func.count(Quiz.id)).where(Quiz.published.is_(True))) or 0

    def quizzes_passed(self, user_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(QuizAttempt.id)).where(
                    QuizAttempt.user_id == user_id, QuizAttempt.passed.is_(True)
                )
            ) or 0
        )

    def points(self, user_id: int) -> int:
        lessons = self.lessons_completed(user_id) * 10
        quizzes = self.quizzes_passed(user_id) * 25
        attempts = (
            self.db.scalar(
                select(func.count(SimulatorAttempt.id)).where(
                    SimulatorAttempt.user_id == user_id, SimulatorAttempt.correct.is_(True)
                )
            ) or 0
        )
        return lessons + quizzes + attempts * 5

    def add_quiz(self, data: dict, questions: list[dict]) -> Quiz:
        quiz = Quiz(
            slug=data["slug"], title=data["title"], category=data.get("category", "general"),
            description=data.get("description"), pass_percent=data.get("pass_percent", 80.0),
        )
        for i, q in enumerate(questions):
            quiz.questions.append(QuizQuestion(
                text=q["text"], options=q["options"], correct_index=q["correct_index"],
                explanation=q.get("explanation"), order=i,
            ))
        self.db.add(quiz)
        self.db.flush()
        return quiz

    def add_lesson(self, data: dict) -> Lesson:
        lesson = Lesson(**data)
        self.db.add(lesson)
        self.db.flush()
        return lesson

    def add_scenario(self, data: dict) -> SimulatorScenario:
        scenario = SimulatorScenario(**data)
        self.db.add(scenario)
        self.db.flush()
        return scenario
