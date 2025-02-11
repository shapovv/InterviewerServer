from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql://interviewer:interviewer@localhost:5432/interviewerdatabase"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание таблиц (если нужно вручную запускать)
if __name__ == "__main__":
    print("Создаем таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")
