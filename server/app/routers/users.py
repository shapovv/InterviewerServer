from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from server.app.utils.db.models import User
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from server.app.schemas.user import UserResponse, UserUpdate

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Возвращает данные текущего (авторизованного) пользователя.
    """
    return current_user


@user_router.get("/", response_model=list[UserResponse])
def get_all_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Возвращает список всех пользователей (доступно только админу).
    Пример: проверяем current_user.email == "admin@example.com"
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    users = db.query(User).all()
    return users


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
        user_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Возвращает информацию о пользователе по его UUID.
    user_id мы указываем как UUID, чтобы FastAPI автоматически конвертировал.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user


@user_router.put("/me", response_model=UserResponse)
def update_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Позволяет пользователю обновить свои данные:
      - email
      - name
      - date_of_birth
      - gender
      - grade
    """

    if user_update.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Этот email уже используется")
        current_user.email = user_update.email

    if user_update.name:
        current_user.name = user_update.name

    if user_update.date_of_birth is not None:
        current_user.date_of_birth = user_update.date_of_birth

    if user_update.gender is not None:
        current_user.gender = user_update.gender

    if user_update.grade is not None:
        current_user.grade = user_update.grade

    db.commit()
    db.refresh(current_user)
    return current_user



@user_router.delete("/me")
def delete_user(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удаляет текущего пользователя из системы.
    """
    db.delete(current_user)
    db.commit()
    return {"message": "Пользователь успешно удален"}
