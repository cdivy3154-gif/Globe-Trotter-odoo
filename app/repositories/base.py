from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: type[ModelType], session: Session):
        self.model = model
        self.session = session

    def get(self, id: str) -> Optional[ModelType]:
        result = self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.session.delete(obj)
        self.session.flush()

    def count(self) -> int:
        result = self.session.execute(select(func.count(self.model.id)))
        return result.scalar_one()