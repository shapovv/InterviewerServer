from pydantic import BaseModel

class AIRequest(BaseModel):
    question: str  # Вопрос от клиента

class AIResponse(BaseModel):
    answer: str  # Ответ от OpenAI

class InterviewRequest(BaseModel):
    answer: str  # Ответ пользователя

class InterviewResponse(BaseModel):
    question: str  # Новый вопрос от ИИ
