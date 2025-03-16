from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from server.app.utils.db.models import Base, User, ChatMessage, Material, UserMaterial, Test, Question, Answer, UserQuestion, UserTestSession

DATABASE_URL = "postgresql://interviewer:interviewer@localhost:5432/interviewerdatabase"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def drop_all_tables():
    meta = MetaData()
    meta.reflect(bind=engine)
    meta.drop_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    print("Удаляем все таблицы...")
    drop_all_tables()
    print("Создаем таблицы...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы.")