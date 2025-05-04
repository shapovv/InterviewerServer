import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine, Column, String, Boolean, DateTime,
    Date, ForeignKey, Text, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    declarative_base, relationship, sessionmaker
)

load_dotenv()

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------
# Таблица пользователей
# ---------------------------------------------------------
class User(Base):
    __tablename__ = 'users'

    # Генерация UUID (используется postgresql.UUID + python-uuid)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)  # 'male' / 'female' / 'other' / ...
    grade = Column(String, nullable=True)   # 'junior' / 'middle' / 'senior' / ...

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Связи (relationship)
    chat_messages = relationship('ChatMessage', back_populates='user')
    user_materials = relationship('UserMaterial', back_populates='user')
    test_sessions = relationship('UserTestSession', back_populates='user')
    user_questions = relationship('UserQuestion', back_populates='user')


# ---------------------------------------------------------
# Логи переписки с ИИ
# ---------------------------------------------------------
class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    role = Column(String, nullable=False, default='user')  # 'user' или 'assistant'
    message_text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False)

    # Связь
    user = relationship('User', back_populates='chat_messages')


# ---------------------------------------------------------
# Учебные материалы
# ---------------------------------------------------------
class Material(Base):
    __tablename__ = 'materials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    level = Column(String, nullable=True)   # 'junior' / 'middle' / 'senior' / ...
    content = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Связь (через промежуточную таблицу UserMaterial)
    user_materials = relationship('UserMaterial', back_populates='material')


# ---------------------------------------------------------
# Связь "пользователь - материал"
# ---------------------------------------------------------
class UserMaterial(Base):
    """
    Хранит индивидуальные отметки по материалу (например, лайк).
    """
    __tablename__ = 'user_materials'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    material_id = Column(UUID(as_uuid=True), ForeignKey('materials.id'), nullable=False)

    is_liked = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False)

    # Связи
    user = relationship('User', back_populates='user_materials')
    material = relationship('Material', back_populates='user_materials')


# ---------------------------------------------------------
# Тесты
# ---------------------------------------------------------
class Test(Base):
    __tablename__ = 'tests'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Связь (один тест -> много вопросов)
    questions = relationship('Question', back_populates='test')


# ---------------------------------------------------------
# Вопросы
# ---------------------------------------------------------
class Question(Base):
    __tablename__ = 'questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey('tests.id'), nullable=False)

    topic = Column(String, nullable=True)
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Связи
    test = relationship('Test', back_populates='questions')
    answers = relationship('Answer', back_populates='question')
    user_questions = relationship('UserQuestion', back_populates='question')


# ---------------------------------------------------------
# Варианты ответов
# ---------------------------------------------------------
class Answer(Base):
    __tablename__ = 'answers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'), nullable=False)

    text = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    # Связь
    question = relationship('Question', back_populates='answers')


# ---------------------------------------------------------
# Статистика: пользователь - вопрос
# ---------------------------------------------------------
class UserQuestion(Base):
    """
    Фиксирует, как пользователь ответил на конкретный вопрос.
    """
    __tablename__ = 'user_questions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey('questions.id'), nullable=False)

    selected_answer_id = Column(UUID(as_uuid=True), ForeignKey('answers.id'), nullable=True)
    is_correct = Column(Boolean, default=False)

    answered_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Связи
    user = relationship('User', back_populates='user_questions')
    question = relationship('Question', back_populates='user_questions')
    selected_answer = relationship('Answer')


# ---------------------------------------------------------
# Сессии прохождения теста
# ---------------------------------------------------------
class UserTestSession(Base):
    __tablename__ = 'user_test_sessions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    test_id = Column(UUID(as_uuid=True), ForeignKey('tests.id'), nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)  # nullable=True — чтобы избежать ошибки при миграции

    total_time_seconds = Column(Integer, nullable=True)  # исправлено
    is_completed = Column(Boolean, default=False, nullable=False)  # исправлено

    # Связи
    user = relationship('User', back_populates='test_sessions')
    # Можно при необходимости связать тест напрямую:
    # test = relationship('Test')


# ---------------------------------------------------------
# Функция для инициализации схемы (создаёт таблицы)
# ---------------------------------------------------------
def init_db():
    Base.metadata.create_all(bind=engine)

