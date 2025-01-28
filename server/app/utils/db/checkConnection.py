from sqlalchemy import create_engine

DATABASE_URL = "postgresql://interviewer:interviewer@localhost:5432/interviewerdatabase"

engine = create_engine(DATABASE_URL)

try:
    # Проверяем соединение
    connection = engine.connect()
    print("Соединение с базой данных успешно установлено!")
    connection.close()
except Exception as e:
    print("Ошибка подключения к базе данных:", e)
