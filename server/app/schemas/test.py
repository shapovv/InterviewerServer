from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

# Создание теста
class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None

# Обновление теста
class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# Ответ при получении теста
class TestResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Или orm_mode=True в более старых версиях
