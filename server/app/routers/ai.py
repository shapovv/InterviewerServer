import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from together import Together
from server.app.schemas.ai import AIRequest, AIResponse, InterviewRequest, InterviewResponse
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY не найден в переменных окружения")

client = Together(api_key=TOGETHER_API_KEY)

ai_router = APIRouter(prefix="/ai", tags=["AI"])

# Сессии чатов (переделать на хранение в таблицах)
chat_sessions = {}

@ai_router.post("/ask", response_model=AIResponse)
def ask_together_ai(request: AIRequest):
    """Отправляет запрос в Together.ai и возвращает ответ."""
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": request.question}]
        )
        answer = response.choices[0].message.content
        return AIResponse(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Together.ai: {str(e)}")



@ai_router.post("/interview", response_model=InterviewResponse)
def interview_chat(request: InterviewRequest, db: Session = Depends(get_db),
                   current_user: dict = Depends(get_current_user)):
    """ Чат с ИИ-интервьюером, который задает вопросы по Swift """

    user_id = current_user.id  # Используем ID пользователя для чата
    if user_id not in chat_sessions:
        chat_sessions[user_id] = [
            {"role": "system",
             "content": "Ты интервьюер по iOS-разработке. Задавай вопросы по Swift и анализируй ответы пользователя."}
        ]

    # Добавляем ответ пользователя в контекст
    chat_sessions[user_id].append({"role": "user", "content": request.answer})

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=chat_sessions[user_id]
        )
        bot_reply = response.choices[0].message.content  # Ответ ИИ

        # Добавляем ответ бота в историю чата
        chat_sessions[user_id].append({"role": "assistant", "content": bot_reply})

        return InterviewResponse(question=bot_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Together.ai: {str(e)}")
