from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from server.app.utils.db.models import User
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from server.app.schemas.user import UserResponse

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    """ Возвращает данные текущего пользователя """
    return current_user
