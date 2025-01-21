from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class UserLogin(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login(user: UserLogin):
    return {"message": "User logged in successfully"}
