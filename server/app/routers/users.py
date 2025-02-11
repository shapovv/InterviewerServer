from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from server.app.utils.db.models import User
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from server.app.schemas.user import UserResponse, UserUpdate

user_router = APIRouter(prefix="/users", tags=["Users"])

# ✅ Получение текущего пользователя
@user_router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """Возвращает данные текущего пользователя"""
    return current_user

# ✅ Получение списка всех пользователей (Только для админа)
@user_router.get("/", response_model=list[UserResponse])
def get_all_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Возвращает список всех пользователей (доступно только админу)"""
    if current_user.email != "admin@example.com":  # Пример проверки
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    users = db.query(User).all()
    return users

# ✅ Получение пользователя по ID
@user_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Возвращает информацию о пользователе по ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

# ✅ Обновление данных пользователя
@user_router.put("/me", response_model=UserResponse)
def update_user(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Позволяет пользователю обновить свой email или имя"""
    if user_update.email:
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Этот email уже используется")

        current_user.email = user_update.email

    if user_update.name:
        current_user.name = user_update.name

    db.commit()
    db.refresh(current_user)
    return current_user

# ✅ Удаление пользователя
@user_router.delete("/me")
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Удаляет текущего пользователя"""
    db.delete(current_user)
    db.commit()
    return {"message": "Пользователь успешно удален"}
