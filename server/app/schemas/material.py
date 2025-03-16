from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class MaterialCreate(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content: Optional[str] = None
    level: Optional[str] = None

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content: Optional[str] = None
    level: Optional[str] = None

class MaterialResponse(BaseModel):
    id: UUID
    title: str
    subtitle: Optional[str]
    content: Optional[str]
    level: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MaterialLikeRequest(BaseModel):
    is_liked: bool
