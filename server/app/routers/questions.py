from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from server.app.utils.db.setup import get_db
from server.app.utils.db.models import User, Test, Question, Answer
from server.app.routers.auth import get_current_user
from server.app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    AnswerCreate, AnswerUpdate, AnswerResponse
)

questions_router = APIRouter(tags=["Questions and Answers"])

# ------------------------------------------------------------------
# 4.1. Получение списка вопросов по тесту
# GET /tests/{test_id}/questions
# ------------------------------------------------------------------
@questions_router.get("/tests/{test_id}/questions", response_model=List[QuestionResponse])
def get_questions_by_test(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает список всех вопросов, принадлежащих указанному тесту.
    По желанию можно добавить пагинацию, фильтры, и т.д.
    """
    # Проверяем, существует ли такой тест
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    questions = db.query(Question).filter(Question.test_id == test_id).all()
    return questions


# ------------------------------------------------------------------
# 4.2. Получение одного вопроса
# GET /questions/{question_id}
# ------------------------------------------------------------------
@questions_router.get("/questions/{question_id}", response_model=QuestionResponse)
def get_question_by_id(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает детальную информацию о вопросе по его UUID.
    Можно дополнительно отдавать список ответов (через другую схему).
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    return question


# ------------------------------------------------------------------
# 4.3.1. Создание вопроса (админ)
# POST /tests/{test_id}/questions
# ------------------------------------------------------------------
@questions_router.post("/tests/{test_id}/questions", response_model=QuestionResponse)
def create_question_for_test(
    test_id: UUID,
    question_data: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт новый вопрос внутри указанного теста (только админ).
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    new_question = Question(
        test_id=test.id,
        topic=question_data.topic,
        question_text=question_data.question_text,
        explanation=question_data.explanation
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


# ------------------------------------------------------------------
# 4.3.2. Обновление вопроса (админ)
# PUT /questions/{question_id}
# ------------------------------------------------------------------
@questions_router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: UUID,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновляет поля (topic, question_text, explanation) у существующего вопроса.
    Только админ.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    if question_data.topic is not None:
        question.topic = question_data.topic
    if question_data.question_text is not None:
        question.question_text = question_data.question_text
    if question_data.explanation is not None:
        question.explanation = question_data.explanation

    db.commit()
    db.refresh(question)
    return question


# ------------------------------------------------------------------
# 4.3.3. Удаление вопроса (админ)
# DELETE /questions/{question_id}
# ------------------------------------------------------------------
@questions_router.delete("/questions/{question_id}")
def delete_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет вопрос по UUID (только админ).
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    db.delete(question)
    db.commit()
    return {"detail": "Вопрос удалён"}


# ------------------------------------------------------------------
# 4.4.1. GET /questions/{question_id}/answers
#      Получение всех ответов для вопроса
# ------------------------------------------------------------------
@questions_router.get("/questions/{question_id}/answers", response_model=List[AnswerResponse])
def get_answers_for_question(
    question_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Возвращает все варианты ответов, которые принадлежат указанному вопросу.
    """
    # Проверяем, что вопрос существует
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    return answers


# ------------------------------------------------------------------
# 4.4.2. POST /questions/{question_id}/answers (админ)
#      Создание нового варианта ответа
# ------------------------------------------------------------------
@questions_router.post("/questions/{question_id}/answers", response_model=AnswerResponse)
def create_answer_for_question(
    question_id: UUID,
    answer_data: AnswerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт новый вариант ответа в конкретном вопросе (только админ).
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    # Проверяем, что вопрос существует
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    new_answer = Answer(
        question_id=question.id,
        text=answer_data.text,
        is_correct=answer_data.is_correct
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return new_answer


# ------------------------------------------------------------------
# 4.4.3. PUT /answers/{answer_id} (админ)
#      Обновление варианта ответа
# ------------------------------------------------------------------
@questions_router.put("/answers/{answer_id}", response_model=AnswerResponse)
def update_answer(
    answer_id: UUID,
    answer_data: AnswerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновляет текст или флаг is_correct у конкретного варианта ответа.
    Только админ.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Ответ не найден")

    if answer_data.text is not None:
        answer.text = answer_data.text
    if answer_data.is_correct is not None:
        answer.is_correct = answer_data.is_correct

    db.commit()
    db.refresh(answer)
    return answer


# ------------------------------------------------------------------
# 4.4.4. DELETE /answers/{answer_id} (админ)
#      Удаление варианта ответа
# ------------------------------------------------------------------
@questions_router.delete("/answers/{answer_id}")
def delete_answer(
    answer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет конкретный вариант ответа (только админ).
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Ответ не найден")

    db.delete(answer)
    db.commit()
    return {"detail": "Вариант ответа удалён"}
