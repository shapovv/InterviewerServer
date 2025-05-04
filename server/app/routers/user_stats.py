from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict
from datetime import datetime, timezone

from server.app.utils.db.setup import get_db
from server.app.utils.db.models import (
    User, UserTestSession, UserQuestion, Question
)
from server.app.routers.auth import get_current_user
from server.app.schemas.user_stat import (
    UserTestsStatsResponse,
    UserQuestionsStatsResponse,
    TopicStats
)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from server.app.utils.db.setup import get_db
from server.app.utils.db.models import User, UserTestSession, UserQuestion
from server.app.routers.auth import get_current_user
from server.app.schemas.user_stat import TestSessionEntry, UserStatsForLeaderboard

user_stats_router = APIRouter(tags=["User Stats"])


# ------------------------------------------------------------------------------
# 6.1. Статистика пользователя о тестах
# GET /users/me/tests/stats
# ------------------------------------------------------------------------------
@user_stats_router.get("/users/me/tests/stats", response_model=UserTestsStatsResponse)
def get_user_tests_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Считает общее число пройденных тестов (is_completed = true),
    среднее/максимальное/минимальное время прохождения,
    а также суммарное количество правильных/неправильных ответов (по всем тестам).
    """

    # 1) Находим все завершённые сессии пользователя
    sessions = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.is_completed == True
    ).all()

    total_tests_completed = len(sessions)

    if total_tests_completed == 0:
        # если пользователь не завершил ни одного теста
        return UserTestsStatsResponse(
            total_tests_completed=0,
            average_time_seconds=None,
            max_time_seconds=None,
            min_time_seconds=None,
            total_correct_answers=0,
            total_wrong_answers=0
        )

    # 2) считаем время
    times = [s.total_time_seconds for s in sessions if s.total_time_seconds is not None]
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
    else:
        avg_time = 0.0
        max_time = 0
        min_time = 0

    # 3) считаем количество правильных/неправильных ответов
    # Для этого найдём все UserQuestion, где user_id = current_user.id
    # Можно не фильтровать по test_id, т.к. хотим суммарно по всем тестам.
    user_questions = db.query(UserQuestion).filter(
        UserQuestion.user_id == current_user.id
    ).all()

    total_correct_answers = sum(1 for uq in user_questions if uq.is_correct)
    total_wrong_answers = len(user_questions) - total_correct_answers

    return UserTestsStatsResponse(
        total_tests_completed=total_tests_completed,
        average_time_seconds=round(avg_time, 2),
        max_time_seconds=max_time,
        min_time_seconds=min_time,
        total_correct_answers=total_correct_answers,
        total_wrong_answers=total_wrong_answers
    )


# ------------------------------------------------------------------------------
# 6.2. Детализированная статистика по вопросам
# GET /users/me/questions/stats
# ------------------------------------------------------------------------------
@user_stats_router.get("/users/me/questions/stats", response_model=UserQuestionsStatsResponse)
def get_user_questions_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает суммарное количество правильных/неправильных ответов,
    а также детальную статистику по "topic" (поле вопроса).
    Формат:
    {
      "total_correct_answers": 10,
      "total_wrong_answers": 5,
      "by_topic": {
         "Алгоритмы": {"correct": 3, "wrong": 2},
         "Основы Swift": {"correct": 7, "wrong": 3}
      }
    }
    """
    # Получаем все записи UserQuestion для этого пользователя
    user_questions = db.query(UserQuestion).join(Question, Question.id == UserQuestion.question_id).filter(
        UserQuestion.user_id == current_user.id
    ).all()

    total_correct = sum(1 for uq in user_questions if uq.is_correct)
    total_wrong = len(user_questions) - total_correct

    # Группируем по теме (Question.topic)
    # user_questions[i].question.topic
    topic_stats: Dict[str, {"correct": int, "wrong": int}] = {}

    for uq in user_questions:
        topic = uq.question.topic if uq.question.topic else "No Topic"
        if topic not in topic_stats:
            topic_stats[topic] = {"correct": 0, "wrong": 0}
        if uq.is_correct:
            topic_stats[topic]["correct"] += 1
        else:
            topic_stats[topic]["wrong"] += 1

    # Преобразуем в удобную модель
    by_topic_result = {}
    for topic, data in topic_stats.items():
        by_topic_result[topic] = TopicStats(correct=data["correct"], wrong=data["wrong"])

    return UserQuestionsStatsResponse(
        total_correct_answers=total_correct,
        total_wrong_answers=total_wrong,
        by_topic=by_topic_result
    )

@user_stats_router.get("/users/me/sessions", response_model=List[TestSessionEntry])
def get_user_test_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sessions = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.is_completed == True
    ).all()

    result = []
    for session in sessions:
        question_ids = [q.id for q in session.test.questions]
        user_questions = db.query(UserQuestion).filter(
            UserQuestion.user_id == current_user.id,
            UserQuestion.question_id.in_(question_ids)
        ).all()

        correct = sum(1 for q in user_questions if q.is_correct)
        incorrect = len(user_questions) - correct
        result.append(TestSessionEntry(
            correct_answers=correct,
            incorrect_answers=incorrect,
            duration=session.total_time_seconds or 0
        ))

    return result


@user_stats_router.get("/leaderboard", response_model=List[UserStatsForLeaderboard])
def get_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).all()
    result = []

    for user in users:
        sessions = db.query(UserTestSession).filter(
            UserTestSession.user_id == user.id,
            UserTestSession.is_completed == True
        ).all()

        if not sessions:
            continue

        question_ids = db.query(UserQuestion).filter(UserQuestion.user_id == user.id).all()
        correct = sum(1 for q in question_ids if q.is_correct)
        total_time = sum(s.total_time_seconds or 0 for s in sessions)

        result.append(UserStatsForLeaderboard(
            name=user.name or user.email,
            total_correct_answers=correct,
            total_time_seconds=total_time
        ))

    return result