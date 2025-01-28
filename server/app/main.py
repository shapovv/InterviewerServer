from fastapi import FastAPI
from server.app.routers import users, tasks
from server.app.utils.db.models import SessionLocal, User, Task, UserTask, Notification

app = FastAPI()

# Подключение маршрутов
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
