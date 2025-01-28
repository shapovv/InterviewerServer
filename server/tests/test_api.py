import sys
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from server.app.main import app
from server.app.utils.db.models import SessionLocal, Base, engine, User, Task
from sqlalchemy.orm import sessionmaker

# Добавляем корень проекта в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Создаем тестовую базу данных
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)  # Создаем таблицы
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Удаляем таблицы после тестов


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


# Тест: Создание пользователя
def test_create_user(client):
    response = client.post("/users/", json={
        "email": "testuser@example.com",
        "password": "testpassword",
        "name": "Test User"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"


# Тест: Получение списка пользователей
def test_read_users(client):
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Тест: Создание задачи
def test_create_task(client):
    response = client.post("/tasks/", json={
        "title": "Solve Algorithm",
        "description": "Write a solution for the given problem",
        "difficulty": "Medium"
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Solve Algorithm"


# Тест: Получение списка задач
def test_read_tasks(client):
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Тест: Удаление задачи
def test_delete_task(client):
    task_response = client.post("/tasks/", json={
        "title": "Task to Delete",
        "description": "This task will be deleted",
        "difficulty": "Easy"
    })
    task_id = task_response.json()["id"]

    delete_response = client.delete(f"/tasks/{task_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["detail"] == "Task deleted"


# Запуск тестов
if __name__ == "__main__":
    pytest.main()
