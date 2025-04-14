import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from together import Together
from server.app.schemas.ai import AIRequest, AIResponse, InterviewRequest, InterviewResponse
from server.app.utils.db.models import ChatMessage
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
def interview_chat(
    request: InterviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    max_history: int = 15  # глубина истории
):
    """ Чат с ИИ-интервьюером, который задает вопросы по Swift """

    # Загружаем последние max_history сообщений из БД
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(max_history)
        .all()
    )

    # Инвертируем порядок (от старых к новым) и превращаем в messages для Together
    history_messages = [
        {"role": msg.role, "content": msg.message_text}
        for msg in reversed(history)
    ]

    # Добавляем системный промпт при начале диалога
    if not history_messages or history_messages[0]["role"] != "system":
        history_messages.insert(0, {
            "role": "system",
            "content": "Ты интервьюер по iOS-разработке. Задавай вопросы по Swift и анализируй ответы пользователя."
        })

    # Добавляем ответ пользователя
    history_messages.append({"role": "user", "content": request.answer})

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=history_messages
        )
        bot_reply = response.choices[0].message.content

        # Сохраняем user-реплику
        db.add(ChatMessage(
            user_id=current_user.id,
            role="user",
            message_text=request.answer
        ))

        # Сохраняем assistant-ответ
        db.add(ChatMessage(
            user_id=current_user.id,
            role="assistant",
            message_text=bot_reply
        ))

        db.commit()

        return InterviewResponse(question=bot_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Together.ai: {str(e)}")
