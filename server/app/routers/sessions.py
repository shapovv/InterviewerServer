from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import func

from server.app.utils.db.setup import get_db
from server.app.utils.db.models import (
    User, Test, Question, Answer, UserTestSession, UserQuestion
)
from server.app.routers.auth import get_current_user

from server.app.schemas.test_session import (
    StartTestResponse,
    AnswerQuestionRequest,
    AnswerQuestionResponse,
    FinishTestResponse,
    MyTestStatsResponse,
    TestStatsResponse
)

sessions_router = APIRouter(tags=["Test Sessions"])

# -------------------------------------------------------------
# 5.1. Начало прохождения теста
# POST /tests/{test_id}/start
# -------------------------------------------------------------
@sessions_router.post("/tests/{test_id}/start", response_model=StartTestResponse)
def start_test(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт запись в UserTestSession для текущего пользователя, ставит start_time.
    Возвращает ID этой сессии (session_id) и время старта.
    """
    # Проверяем, существует ли тест
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    # Проверим, нет ли уже незавершённой сессии
    existing_session = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.test_id == test_id,
        UserTestSession.is_completed == False
    ).first()
    if existing_session:
        # Если вы хотите запрещать параллельные сессии, можно вернуть 400
        raise HTTPException(status_code=400, detail="У вас уже есть незавершённый тест")

    new_session = UserTestSession(
        user_id=current_user.id,
        test_id=test_id,
        start_time=datetime.now(timezone.utc),
        is_completed=False
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return StartTestResponse(
        session_id=new_session.id,
        start_time=new_session.start_time
    )


# -------------------------------------------------------------
# 5.2. Ответ пользователя на вопрос
# POST /tests/{test_id}/questions/{question_id}/answer
# -------------------------------------------------------------
@sessions_router.post("/tests/{test_id}/questions/{question_id}/answer", response_model=AnswerQuestionResponse)
def answer_question(
    test_id: UUID,
    question_id: UUID,
    answer_req: AnswerQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Сохраняет ответ пользователя на вопрос.
    - selected_answer_id: UUID
    - Опционально сразу проверяет правильность ответа.
    """
    # Проверяем, есть ли незавершённая сессия у пользователя для этого теста
    session = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.test_id == test_id,
        UserTestSession.is_completed == False
    ).first()
    if not session:
        raise HTTPException(status_code=400, detail="Нет активной сессии для этого теста")

    # Проверяем, что question_id действительно относится к этому тесту
    question = db.query(Question).filter(Question.id == question_id, Question.test_id == test_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден в этом тесте")

    # Проверяем, что selected_answer_id действительно принадлежит этому вопросу
    answer = db.query(Answer).filter(Answer.id == answer_req.selected_answer_id, Answer.question_id == question_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Ответ не найден или не соответствует вопросу")

    # Определяем, верен ли ответ
    is_correct = answer.is_correct

    # Проверяем, отвечал ли пользователь уже на этот вопрос (можно разрешить перезапись)
    user_question = db.query(UserQuestion).filter(
        UserQuestion.user_id == current_user.id,
        UserQuestion.question_id == question_id
    ).first()

    if not user_question:
        # Создаём запись
        user_question = UserQuestion(
            user_id=current_user.id,
            question_id=question_id,
            selected_answer_id=answer.id,
            is_correct=is_correct
        )
        db.add(user_question)
    else:
        # Обновляем запись (если вы хотите разрешить менять ответ)
        user_question.selected_answer_id = answer.id
        user_question.is_correct = is_correct
        user_question.answered_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(user_question)

    return AnswerQuestionResponse(
        user_question_id=user_question.id,
        is_correct=user_question.is_correct,
        answered_at=user_question.answered_at
    )


# -------------------------------------------------------------
# 5.3. Завершение прохождения теста
# POST /tests/{test_id}/finish
# -------------------------------------------------------------
@sessions_router.post("/tests/{test_id}/finish", response_model=FinishTestResponse)
def finish_test(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Устанавливает end_time и total_time_seconds в UserTestSession.
    Ставит is_completed = true.
    Возвращает статистику: кол-во правильных и неправильных ответов.
    """
    session = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.test_id == test_id,
        UserTestSession.is_completed == False
    ).first()
    if not session:
        raise HTTPException(status_code=400, detail="Нет активной сессии или тест уже завершён")

    # Ставим end_time, считаем total_time
    end_time = datetime.now(timezone.utc)
    start_time = session.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)

    time_spent = int((end_time - start_time).total_seconds())
    session.end_time = end_time
    session.total_time_seconds = time_spent
    session.is_completed = True
    db.commit()

    # Считаем кол-во правильных/неправильных ответов
    user_questions = db.query(UserQuestion).filter(
        UserQuestion.user_id == current_user.id,
        UserQuestion.question_id.in_(
            db.query(Question.id).filter(Question.test_id == test_id)
        )
    ).all()

    correct_answers_count = sum(1 for uq in user_questions if uq.is_correct)
    wrong_answers_count = len(user_questions) - correct_answers_count

    return FinishTestResponse(
        session_id=session.id,
        end_time=end_time,
        total_time_seconds=time_spent,
        correct_answers_count=correct_answers_count,
        wrong_answers_count=wrong_answers_count
    )


# -------------------------------------------------------------
# 5.4. Получение статистики прохождения (только для текущего юзера)
# GET /tests/{test_id}/stats/me
# -------------------------------------------------------------
@sessions_router.get("/tests/{test_id}/stats/me", response_model=MyTestStatsResponse)
def get_my_test_stats(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает для текущего пользователя:
    - прошёл ли тест (is_completed),
    - total_time_seconds,
    - кол-во правильных и неправильных ответов
    """
    session = db.query(UserTestSession).filter(
        UserTestSession.user_id == current_user.id,
        UserTestSession.test_id == test_id
    ).order_by(UserTestSession.start_time.desc()).first()

    if not session:
        # Пользователь ещё не проходил тест
        return MyTestStatsResponse(
            is_completed=False,
            total_time_seconds=None,
            correct_answers_count=0,
            wrong_answers_count=0
        )

    # Считаем ответы
    user_questions = db.query(UserQuestion).filter(
        UserQuestion.user_id == current_user.id,
        UserQuestion.question_id.in_(
            db.query(Question.id).filter(Question.test_id == test_id)
        )
    ).all()

    correct_answers_count = sum(1 for uq in user_questions if uq.is_correct)
    wrong_answers_count = len(user_questions) - correct_answers_count

    return MyTestStatsResponse(
        is_completed=session.is_completed,
        total_time_seconds=session.total_time_seconds,
        correct_answers_count=correct_answers_count,
        wrong_answers_count=wrong_answers_count
    )


# -------------------------------------------------------------
# 5.5. Общая статистика (для админа/препода)
# GET /tests/{test_id}/stats
# -------------------------------------------------------------
@sessions_router.get("/tests/{test_id}/stats", response_model=TestStatsResponse)
def get_test_stats(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Общая статистика по всем пользователям:
      - total_users_attempted
      - avg_correct_answers
      - avg_wrong_answers
      - avg_time_seconds
    """
    # Проверка на роль админа
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Все сессии для данного теста
    sessions = db.query(UserTestSession).filter(UserTestSession.test_id == test_id, UserTestSession.is_completed == True).all()
    if not sessions:
        # Если никто не проходил тест, то статистики нет
        return TestStatsResponse(
            total_users_attempted=0,
            avg_correct_answers=0,
            avg_wrong_answers=0,
            avg_time_seconds=0
        )

    user_ids = [s.user_id for s in sessions]

    # Собираем все ответы (UserQuestion), относящиеся к этому тесту для указанных пользователей
    user_questions = db.query(UserQuestion).filter(
        UserQuestion.user_id.in_(user_ids),
        UserQuestion.question_id.in_(
            db.query(Question.id).filter(Question.test_id == test_id)
        )
    ).all()

    # Подсчитаем correct/total по каждому пользователю
    # либо считаем в лоб, если пользователей немного:
    # correct = кол-во user_questions где is_correct == True
    correct_count = sum(1 for uq in user_questions if uq.is_correct)
    total_answers = len(user_questions)
    wrong_count = total_answers - correct_count

    total_users_attempted = len(set(user_ids))

    # среднее количество правильных ответов на пользователя
    # для корректного расчёта можно сгруппировать по user_id,
    # но для упрощения возьмём "суммарные correct / кол-во пользователей"
    avg_correct_answers = 0.0
    avg_wrong_answers = 0.0

    if total_users_attempted > 0:
        avg_correct_answers = correct_count / total_users_attempted
        avg_wrong_answers = wrong_count / total_users_attempted

    # среднее время прохождения
    times = [s.total_time_seconds for s in sessions if s.total_time_seconds is not None]
    if times:
        avg_time_seconds = sum(times) / len(times)
    else:
        avg_time_seconds = 0.0

    return TestStatsResponse(
        total_users_attempted=total_users_attempted,
        avg_correct_answers=round(avg_correct_answers, 2),
        avg_wrong_answers=round(avg_wrong_answers, 2),
        avg_time_seconds=round(avg_time_seconds, 2)
    )
