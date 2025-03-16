from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from server.app.utils.db.models import Material, UserMaterial, User
from server.app.utils.db.setup import get_db
from server.app.routers.auth import get_current_user
from server.app.schemas.material import (
    MaterialResponse,
    MaterialCreate,
    MaterialUpdate,
    MaterialLikeRequest
)

materials_router = APIRouter(prefix="/materials", tags=["Materials"])


# -----------------------------------------------------------
# 1.1. GET /materials - список материалов c фильтром
# -----------------------------------------------------------
@materials_router.get("/", response_model=List[MaterialResponse])
def get_materials(
        level: Optional[str] = Query(None, description="Уровень: junior/middle/senior"),
        search: Optional[str] = Query(None, description="Поисковая строка"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # если нужно авторизовать
):
    """
    Возвращает список всех материалов.
    Опциональные параметры:
      - level: фильтрация по уровню (junior/middle/senior)
      - search: поиск по названию/подзаголовку
    """
    query = db.query(Material)

    if level:
        query = query.filter(Material.level == level)

    if search:
        search_pattern = f"%{search}%"
        # поиск по title или subtitle (пример)
        query = query.filter(
            (Material.title.ilike(search_pattern)) |
            (Material.subtitle.ilike(search_pattern))
        )

    materials = query.order_by(Material.created_at.desc()).all()
    return materials


# -----------------------------------------------------------
# 1.2. GET /materials/{material_id} - детальная инфа
# -----------------------------------------------------------
@materials_router.get("/{material_id}", response_model=MaterialResponse)
def get_material_by_id(
        material_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),  # если доступ только авторизованным
):
    """
    Возвращает детальную информацию об учебном материале по его UUID.
    """
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")
    return material


# -----------------------------------------------------------
# 1.3. POST /materials - создание материала (только админ)
# -----------------------------------------------------------
@materials_router.post("/", response_model=MaterialResponse)
def create_material(
        material_data: MaterialCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Создаёт новый материал.
    Доступно только администратору.
    """
    # Пример проверки "админа" по email
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    new_material = Material(
        title=material_data.title,
        subtitle=material_data.subtitle,
        content=material_data.content,
        level=material_data.level
    )
    db.add(new_material)
    db.commit()
    db.refresh(new_material)

    return new_material


# -----------------------------------------------------------
# 1.4. PUT /materials/{material_id} - обновление (только админ)
# -----------------------------------------------------------
@materials_router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
        material_id: UUID,
        material_data: MaterialUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Обновляет поля (title, subtitle, content, level) у существующего материала.
    Доступно только администратору.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")

    if material_data.title is not None:
        material.title = material_data.title
    if material_data.subtitle is not None:
        material.subtitle = material_data.subtitle
    if material_data.content is not None:
        material.content = material_data.content
    if material_data.level is not None:
        material.level = material_data.level

    db.commit()
    db.refresh(material)
    return material


# -----------------------------------------------------------
# 1.5. DELETE /materials/{material_id} - удаление (только админ)
# -----------------------------------------------------------
@materials_router.delete("/{material_id}")
def delete_material(
        material_id: UUID,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удаляет материал по UUID.
    Доступно только администратору.
    """
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")

    db.delete(material)
    db.commit()
    return {"detail": "Материал удалён"}


# -----------------------------------------------------------
# 1.6. POST /materials/{material_id}/like - поставить / снять лайк
# -----------------------------------------------------------
@materials_router.post("/{material_id}/like")
def set_material_like(
        material_id: UUID,
        like_data: MaterialLikeRequest,  # { is_liked: bool }
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Меняет поле is_liked в UserMaterial для текущего пользователя.
    Может принимать is_liked=true/false.
    """
    # Проверяем, что материал существует
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Материал не найден")

    # Проверяем, есть ли уже запись в user_materials
    user_material = db.query(UserMaterial).filter(
        UserMaterial.user_id == current_user.id,
        UserMaterial.material_id == material_id
    ).first()

    if not user_material:
        # если нет - создать запись
        user_material = UserMaterial(
            user_id=current_user.id,
            material_id=material_id,
            is_liked=like_data.is_liked
        )
        db.add(user_material)
    else:
        # если есть - просто обновить флаг
        user_material.is_liked = like_data.is_liked

    db.commit()
    return {"detail": f"Лайк установлен в состояние {like_data.is_liked}"}


# -----------------------------------------------------------
# 1.7. GET /users/me/materials/liked - список лайкнутых пользователем
# -----------------------------------------------------------
@materials_router.get("/my/liked", response_model=List[MaterialResponse])
def get_liked_materials(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Возвращает все материалы, которые текущий пользователь лайкнул (is_liked = true).
    """
    # находим все user_materials с is_liked = True
    user_materials = db.query(UserMaterial).filter(
        UserMaterial.user_id == current_user.id,
        UserMaterial.is_liked == True
    ).all()

    # Вытащим из них IDs материалов
    liked_ids = [um.material_id for um in user_materials]

    # Загрузим все материалы с этими ID
    materials = db.query(Material).filter(Material.id.in_(liked_ids)).all()
    return materials
