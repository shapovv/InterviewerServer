from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from server.app.utils.db.models import Test, User
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from server.app.schemas.test import TestCreate, TestUpdate, TestResponse

tests_router = APIRouter(prefix="/tests", tags=["Tests"])

# -----------------------------------------------------------
# 3.1. GET /tests - список тестов (с опциональным поиском)
# -----------------------------------------------------------
@tests_router.get("/", response_model=List[TestResponse])
def get_tests(
    search: Optional[str] = Query(None, description="Поиск в названии/описании"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает список всех тестов.
    Опционально можно делать поиск (search) по title или description.
    """
    query = db.query(Test)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Test.title.ilike(pattern)) |
            (Test.description.ilike(pattern))
        )

    tests = query.order_by(Test.created_at.desc()).all()
    return tests


# -----------------------------------------------------------
# 3.2. GET /tests/{test_id} - детальная информация
# -----------------------------------------------------------
@tests_router.get("/{test_id}", response_model=TestResponse)
def get_test_by_id(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Возвращает детальную информацию о тесте по его UUID.
    При желании можно включить список вопросов.
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    return test


# -----------------------------------------------------------
# 3.3. POST /tests - создание теста (только админ)
# -----------------------------------------------------------
@tests_router.post("/", response_model=TestResponse)
def create_test(
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создаёт новый тест.
    Доступно только администратору.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    new_test = Test(
        title=test_data.title,
        description=test_data.description
    )
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


# -----------------------------------------------------------
# 3.4. PUT /tests/{test_id} - обновление (только админ)
# -----------------------------------------------------------
@tests_router.put("/{test_id}", response_model=TestResponse)
def update_test(
    test_id: UUID,
    test_data: TestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновляет поля (title, description) у существующего теста.
    Доступно только администратору.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    if test_data.title is not None:
        test.title = test_data.title
    if test_data.description is not None:
        test.description = test_data.description

    db.commit()
    db.refresh(test)
    return test


# -----------------------------------------------------------
# 3.5. DELETE /tests/{test_id} - удаление (только админ)
# -----------------------------------------------------------
@tests_router.delete("/{test_id}")
def delete_test(
    test_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удаляет тест по UUID.
    Доступно только администратору.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")

    db.delete(test)
    db.commit()
    return {"detail": "Тест удалён"}
