from fastapi import FastAPI
from server.app.routers.auth import auth_router
from server.app.routers.users import user_router
from server.app.routers.ai import ai_router
from server.app.routers.materials import materials_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(ai_router)
app.include_router(materials_router)

@app.get("/")
def root():
    return {"message": "API is running!"}
