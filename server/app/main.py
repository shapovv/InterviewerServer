from fastapi import FastAPI
from server.app.routers.auth import auth_router
from server.app.routers.users import user_router
from server.app.routers.ai import ai_router
from server.app.routers.materials import materials_router
from server.app.routers.tests import tests_router
from server.app.routers.questions import questions_router
from server.app.routers.sessions import sessions_router
from server.app.routers.user_stats import user_stats_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(ai_router)
app.include_router(materials_router)
app.include_router(tests_router)
app.include_router(questions_router)
app.include_router(sessions_router)
app.include_router(user_stats_router)

@app.get("/")
def root():
    return {"message": "API is running!"}
