# InterviewerServer

InterviewerServer — это проект на основе FastAPI, предназначенный для обработки различных функций, таких как управление пользователями, аналитика, уведомления, работа с задачами и интеграция с ИИ-сервисами. Проект построен с учетом модульной архитектуры для масштабируемости и удобства сопровождения.

---

## **Возможности**

1. **Управление пользователями:**
   - Регистрация и авторизация пользователей.
   - Безопасное управление сессиями с использованием JWT (access и refresh токены).
   - Ролевой доступ (пользователь, администратор).

2. **Работа с задачами:**
   - Автоматическая проверка задач и предоставление обратной связи.
   - Несколько режимов тестирования (быстрые тесты, пользовательские сценарии).

3. **Уведомления:**
   - Push-уведомления и обновления в реальном времени через WebSocket.
   - Настраиваемые уведомления.

4. **Интеграция с ИИ:**
   - Интеграция с OpenAI API для работы LLM-ассистента.
   - Поддержка OCR для извлечения текста из изображений.

5. **Аналитика:**
   - Отслеживание поведения пользователей и предоставление персонализированных рекомендаций.
   - Аналитика для администраторов (популярные темы, процент завершения задач).

6. **Панель администратора:**
   - Управление контентом (материалы, задачи).
   - Управление учетными записями пользователей (создание, блокировка, удаление).

---

## **Структура проекта**

```
InterviewerServer/
├── docker/
│   ├── Dockerfile                # Конфигурация для сборки Docker-образа
│   └── docker-compose.yml        # Конфигурация для запуска нескольких сервисов
├── docs/
│   └── README.md                 # Документация проекта
├── requirements.txt              # Зависимости Python
└── server/
    ├── app/
    │   ├── main.py                # Точка входа приложения
    │   ├── routers/               # API маршруты
    │   │   ├── admin.py           # Маршруты администратора
    │   │   ├── analytics.py       # Маршруты аналитики
    │   │   ├── auth.py            # Маршруты аутентификации
    │   │   ├── notifications.py   # Маршруты уведомлений
    │   │   └── tasks.py           # Маршруты задач
    │   ├── services/              # Логика приложений
    │   │   ├── ai_service.py      # Сервис для работы с ИИ
    │   │   ├── notification.py    # Сервис уведомлений
    │   │   └── session.py         # Управление сессиями
    │   ├── utils/                 # Утилитарные модули
    │   │   ├── db.py              # Подключение к базе данных
    │   │   ├── logging.py         # Логирование
    │   │   └── security.py        # Безопасность
    │   ├── static/                # Статические файлы (пусто)
    │   └── templates/             # HTML-шаблоны (пусто)
    ├── migrations/                # Миграции базы данных (пусто)
    └── tests/                     # Юнит-тесты
        ├── test_auth.py           # Тесты аутентификации
        ├── test_notifications.py  # Тесты уведомлений
        └── test_tasks.py          # Тесты задач
```

---

## **Инструкции по настройке**

### **1. Клонирование репозитория**
```bash
git clone https://github.com/yourusername/InterviewerServer.git
cd InterviewerServer
```

### **2. Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Для Linux/Mac
venv\Scripts\activate   # Для Windows
```

### **3. Установка зависимостей**
```bash
pip install -r requirements.txt
```

### **4. Настройка переменных окружения**
Создайте файл `.env` в корне проекта со следующими переменными:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET_KEY=your_secret_key
```

### **5. Запуск сервера**
```bash
uvicorn server.app.main:app --reload
```

API будет доступно по адресу: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## **Тестирование**
Запустите следующую команду для выполнения юнит-тестов:
```bash
pytest
```

---

## **Развёртывание**
1. Сборка Docker-образа:
   ```bash
   docker build -t interviewer_server .
   ```

2. Запуск Docker-контейнера:
   ```bash
   docker run -p 8000:8000 interviewer_server
   ```

---
