"""Learning center schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    category: str
    summary: str | None = None
    content: str
    example: str | None = None
    tips: list[str] | None = None
    reading_time: int
    order: int
    published: bool


class QuizOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    category: str
    description: str | None = None
    pass_percent: float


class QuestionOut(BaseModel):
    id: int
    text: str
    explanation: str | None = None
    options: list[str]
    order: int


class QuizDetailOut(QuizOut):
    questions: list[QuestionOut]


class QuizSubmit(BaseModel):
    answers: list[int]


class QuizResult(BaseModel):
    score_percent: float
    correct_count: int
    total_count: int
    passed: bool
    certificate_code: str | None = None
    explanation: list[dict] = Field(default_factory=list)


class LessonProgressUpdate(BaseModel):
    progress: float = Field(ge=0, le=100)
    completed: bool = False


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    category: str
    difficulty: str
    content: str
    options: list[str]


class ScenarioAnswer(BaseModel):
    scenario_id: int
    chosen_index: int


class ScenarioResult(BaseModel):
    correct: bool
    correct_index: int
    explanation: str | None = None
    red_flags: list[str] | None = None
    streak: int


class ProgressOut(BaseModel):
    lessons_completed: int
    lessons_total: int
    quizzes_passed: int
    quizzes_total: int
    streak: int
    points: int
    level: str
