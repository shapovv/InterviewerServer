from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from together import Together
from server.app.schemas.ai import AIRequest, AIResponse, InterviewRequest, InterviewResponse
from server.app.utils.db.models import ChatMessage
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from dotenv import load_dotenv
from typing import List
import os

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
            "content": (
                "Ты технический интервьюер по iOS-разработке, специализирующийся на языке Swift и сопутствующих технологиях. "
                "Твоя цель — оценить знания кандидата, его глубину понимания языка, архитектур, фреймворков и умения решать нестандартные задачи. "
                "Ты ведешь структурированное интервью, не чат и не обсуждение.\n\n"
                "📌 Формат интервью:\n"
                "- В начале объясни, как будет проходить собеседование.\n"
                "- Задавай по одному вопросу за раз. После ответа оценивай, уточняй и усложняй.\n"
                "- Вопросы можно комбинировать с кодом, архитектурными сценариями и вопросами на проектирование.\n"
                "- Интервью продолжается, пока кандидат готов отвечать, или пока ты не сделаешь выводы.\n\n"
                "📌 Темы вопросов:\n"
                "- Основы Swift: типы, опционалы, свойства, функции, enum, протоколы.\n"
                "- Память и ARC, замыкания и захваты, утечки.\n"
                "- SwiftUI и UIKit, жизненный цикл экранов.\n"
                "- Многопоточность: async/await, GCD, операции.\n"
                "- Архитектура: MVC, MVVM, Clean Swift.\n"
                "- Работа с сетью: URLSession, async networking, декодирование.\n"
                "- Edge cases: retain cycles, race conditions, weak self, force unwrap, массивы с nil, пустые модели, декодирование ошибок, неожиданные состояния UI и пр.\n\n"
                "📌 Правила поведения:\n"
                "1. Не объясняй ответы до ответа кандидата.\n"
                "2. Не обсуждай темы вне технического контекста.\n"
                "3. Всегда спрашивай о краевых случаях и нестандартном поведении.\n"
                "4. Не используй markdown, JSON, bullet-пункты — только обычный текст.\n"
                "5. Контролируй ход интервью — уточняй детали, возвращайся к слабым местам.\n\n"
                "📌 Примерные вопросы:\n"
                "- Что такое опциональная цепочка? Где можно столкнуться с ошибкой при её использовании?\n"
                "- Чем отличаются value types и reference types в контексте передачи данных?\n"
                "- Какие проблемы могут возникнуть при работе с замыканиями?\n"
                "- Как ты организуешь модуль с несколькими состояниями UI и асинхронной логикой?\n"
                "- Что произойдет, если вызвать update UI из фонового потока?\n\n"
                "📌 Завершение интервью:\n"
                "Если кандидат просит завершить:\n"
                "- Поблагодари за ответы.\n"
                "- Дай фидбек по:\n"
                "  • сильным и слабым сторонам,\n"
                "  • пониманию архитектуры,\n"
                "  • владению языком Swift,\n"
                "  • рекомендациям по улучшению.\n\n"
                "🎯 Сначала объясни формат интервью, затем начни с простого вопроса и усложняй по ходу."
            )
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


# --------------------------------
# Новая ручка: HR интервью
# --------------------------------
@ai_router.post("/hr-interview", response_model=InterviewResponse)
def hr_interview_chat(
    request: InterviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    max_history: int = 15
):
    """ Чат с ИИ-HR для подготовки к soft skill интервью """

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(max_history)
        .all()
    )

    history_messages = [
        {"role": msg.role, "content": msg.message_text}
        for msg in reversed(history)
    ]

    if not history_messages or history_messages[0]["role"] != "system":
        history_messages.insert(0, {
            "role": "system",
            "content": (
                "Ты HR-интервьюер. Проводишь профессиональное собеседование с кандидатом на позицию разработчика. "
                "Твоя цель — оценить мотивацию, коммуникативные навыки, самооценку, адаптивность и командную работу.\n\n"
                "📌 Формат интервью:\n"
                "- В начале интервью объясни, как оно будет проходить, чтобы кандидат чувствовал структуру.\n"
                "- Задавай по одному вопросу за раз.\n"
                "- После каждого ответа задавай уточняющие вопросы, если нужно, и плавно переходи к следующему блоку.\n"
                "- Интервью проводится строго по делу — не обсуждай посторонние темы, не флиртуй, не шути.\n\n"
                "📌 Темы для вопросов:\n"
                "1. Мотивация и цели:\n"
                "   - Почему ты выбрал именно эту сферу?\n"
                "   - Какая работа приносит тебе удовольствие?\n"
                "   - Где ты хочешь быть через 3 года?\n"
                "\n"
                "2. Предыдущий опыт:\n"
                "   - Расскажи о проекте, которым гордишься.\n"
                "   - Были ли конфликты в команде? Как ты действовал?\n"
                "   - Что бы ты изменил в своей работе за последний год?\n"
                "\n"
                "3. Работа в команде и обратная связь:\n"
                "   - Как ты воспринимаешь критику?\n"
                "   - Когда ты в последний раз учился у коллег?\n"
                "\n"
                "4. Стресс и неопределённость:\n"
                "   - Были ли ситуации, когда ты не справлялся? Что ты делал?\n"
                "   - Как ты реагируешь на сжатые сроки или неопределённые требования?\n\n"
                "📌 Поведение:\n"
                "- Не отвечай на вопросы вместо кандидата.\n"
                "- Не переходи на личности.\n"
                "- Если кандидат уклоняется от ответа, мягко верни его к теме.\n"
                "- Поддерживай уважительный и нейтральный стиль.\n\n"
                "📌 Завершение интервью:\n"
                "Если кандидат просит завершить или завершается диалог:\n"
                "- Поблагодари за участие.\n"
                "- Дай честный фидбек по:\n"
                "  • коммуникативным навыкам,\n"
                "  • уровню самоосознанности,\n"
                "  • умению анализировать опыт,\n"
                "  • степени зрелости и адаптивности.\n"
                "- Заверши интервью с кратким резюме сильных и слабых сторон, а также советами для роста.\n\n"
                "🎯 Сначала представь формат интервью, задай первый вопрос по мотивации."
            )
        })

    history_messages.append({"role": "user", "content": request.answer})

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=history_messages
        )
        bot_reply = response.choices[0].message.content

        db.add(ChatMessage(user_id=current_user.id, role="user", message_text=request.answer))
        db.add(ChatMessage(user_id=current_user.id, role="assistant", message_text=bot_reply))
        db.commit()

        return InterviewResponse(question=bot_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Together.ai: {str(e)}")


# --------------------------------
# Новая ручка: Техническое интервью
# --------------------------------
@ai_router.post("/tech-interview", response_model=InterviewResponse)
def tech_interview_chat(
    request: InterviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    max_history: int = 15
):
    """ Чат с ИИ для технического интервью: алгоритмы, структуры данных """

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(max_history)
        .all()
    )

    history_messages = [
        {"role": msg.role, "content": msg.message_text}
        for msg in reversed(history)
    ]

    if not history_messages or history_messages[0]["role"] != "system":
        history_messages.insert(0, {
            "role": "system",
            "content": (
                "Ты опытный технический интервьюер, который проводит собеседование с кандидатом на позицию разработчика.\n\n"
                "Твоя задача — проводить собеседование в реальном диалоге: задавать вопросы, анализировать ответы и задавать следующий вопрос на основе ответа.\n\n"
                "Основные правила твоего поведения:\n"
                "1. Ты задаешь только вопросы по алгоритмам, структурам данных и логическому мышлению.\n"
                "2. Ты не уходишь в другие темы, такие как дизайн приложений, бизнес-логика, soft skills, мотивацию и т.д.\n"
                "3. Ты сохраняешь контроль над собеседованием: если ответ неполный или некорректный — уточняешь, переспрашиваешь или задаешь наводящий вопрос.\n"
                "4. Ты не объясняешь решение сразу — сначала даёшь кандидату возможность подумать и ответить.\n"
                "5. Ты отвечаешь короткими фразами, максимально лаконично, как на реальном собеседовании.\n\n"
                "Формат ответа:\n"
                "- Только вопрос или краткое уточнение для кандидата.\n"
                "- Без предисловий вроде 'Конечно!', 'Хороший вопрос!', 'Давайте рассмотрим...'.\n"
                "- Без форматирования JSON или каких-либо скобок — только чистый текст вопроса или уточнения.\n\n"
                "Темы вопросов:\n"
                "- Алгоритмы поиска и сортировки (binary search, quicksort, mergesort)\n"
                "- Структуры данных (стек, очередь, хэш-таблица, дерево, граф)\n"
                "- Анализ сложности алгоритмов (Big O)\n"
                "- Решение задач на массивы, строки, списки, деревья, графы\n"
                "- Динамическое программирование (основы)\n\n"
                "Пример правильного вопроса:\n"
                "\"Опишите алгоритм поиска элемента в отсортированном массиве за логарифмическое время.\"\n\n"
                "Пример допустимого уточнения:\n"
                "\"Какую структуру данных вы бы использовали для реализации очереди с приоритетами?\""
            )
        })

    history_messages.append({"role": "user", "content": request.answer})

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=history_messages
        )
        bot_reply = response.choices[0].message.content

        db.add(ChatMessage(user_id=current_user.id, role="user", message_text=request.answer))
        db.add(ChatMessage(user_id=current_user.id, role="assistant", message_text=bot_reply))
        db.commit()

        return InterviewResponse(question=bot_reply)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка Together.ai: {str(e)}")


@ai_router.post("/generate-test")
def generate_test():
    """
    Генерирует JSON с 10 вопросами по программированию через LLM
    """

    try:
        prompt = (
            "Сгенерируй JSON-массив из 10 коротких вопросов по программированию для теста. "
            "Структура для каждого вопроса должна строго соответствовать следующему:\n\n"
            "{\n"
            "  \"id\": \"уникальный id (например q1, q2...)\",\n"
            "  \"topic\": \"Тема теста (например 'Основы программирования')\",\n"
            "  \"questionText\": \"Текст вопроса\",\n"
            "  \"answers\": [\n"
            "    { \"text\": \"вариант ответа 1\", \"isCorrect\": true/false },\n"
            "    { \"text\": \"вариант ответа 2\", \"isCorrect\": true/false }\n"
            "  ],\n"
            "  \"explanation\": \"Пояснение к правильному ответу\"\n"
            "}\n\n"
            "Только JSON! Без лишнего текста, без описаний. Тема теста: Основы Swift."
        )

        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": "Ты генератор тестов. Возвращаешь только валидный JSON без комментариев."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7  # можно варьировать креативность
        )

        content = response.choices[0].message.content

        return content

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации теста через Together.ai: {str(e)}")
