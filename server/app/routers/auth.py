from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta
from jose import jwt, JWTError
from server.app.utils.db.models import User
from server.app.utils.db.setup import get_db
from server.app.utils.security import hash_password, verify_password, create_access_token
from server.app.schemas.user import UserCreate, UserLogin, Token  # ✅ Теперь Token доступен

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"


@auth_router.post("/register", response_model=UserCreate)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    new_user = User(
        email=user_data.email,
        name=user_data.name,
        password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")

    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """ Декодирует JWT и получает текущего пользователя из БД """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Не удалось проверить учетные данные")
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Некорректный токен")
