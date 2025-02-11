from fastapi import FastAPI
from server.app.routers.auth import auth_router
from server.app.routers.users import user_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)

@app.get("/")
def root():
    return {"message": "API is running!"}
