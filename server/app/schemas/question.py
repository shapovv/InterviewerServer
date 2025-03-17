from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ------------------------------------------------
# Создание вопроса
# ------------------------------------------------
class QuestionCreate(BaseModel):
    topic: Optional[str] = None
    question_text: str
    explanation: Optional[str] = None

# ------------------------------------------------
# Обновление вопроса
# ------------------------------------------------
class QuestionUpdate(BaseModel):
    topic: Optional[str] = None
    question_text: Optional[str] = None
    explanation: Optional[str] = None

# ------------------------------------------------
# Ответ на запрос (вопрос)
# ------------------------------------------------
class QuestionResponse(BaseModel):
    id: UUID
    topic: Optional[str]
    question_text: str
    explanation: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ------------------------------------------------
# Cхемы для Answer
# ------------------------------------------------
class AnswerCreate(BaseModel):
    text: str
    is_correct: bool

class AnswerUpdate(BaseModel):
    text: Optional[str] = None
    is_correct: Optional[bool] = None

class AnswerResponse(BaseModel):
    id: UUID
    text: str
    is_correct: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
