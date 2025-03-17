from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

# -------------------------------------------------------------
# 5.1. Начало прохождения теста (можно вернуть SessionID)
# -------------------------------------------------------------
class StartTestResponse(BaseModel):
    session_id: UUID
    start_time: datetime

# -------------------------------------------------------------
# 5.2. Ответ пользователя на вопрос
# -------------------------------------------------------------
class AnswerQuestionRequest(BaseModel):
    selected_answer_id: UUID

class AnswerQuestionResponse(BaseModel):
    user_question_id: UUID
    is_correct: bool
    answered_at: datetime

# -------------------------------------------------------------
# 5.3. Завершение прохождения теста
# -------------------------------------------------------------
class FinishTestResponse(BaseModel):
    session_id: UUID
    end_time: datetime
    total_time_seconds: int
    correct_answers_count: int
    wrong_answers_count: int

# -------------------------------------------------------------
# 5.4. Личная статистика пользователя
# (возвращаем короткую информацию: прошёл ли тест,
# время прохождения, кол-во правильных/неправильных)
# -------------------------------------------------------------
class MyTestStatsResponse(BaseModel):
    is_completed: bool
    total_time_seconds: Optional[int]
    correct_answers_count: int
    wrong_answers_count: int

# -------------------------------------------------------------
# 5.5. Общая статистика по тесту (для админа)
# -------------------------------------------------------------
class TestStatsResponse(BaseModel):
    total_users_attempted: int
    avg_correct_answers: float
    avg_wrong_answers: float
    avg_time_seconds: float
