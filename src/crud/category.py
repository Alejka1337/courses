from datetime import datetime
from typing import List, Literal, Type, TypeVar, Union

from sqlalchemy.orm import Session

from src.models import CategoryOrm
from src.schemas.category import CategoryCreate, CategoryUpdate

T = TypeVar("T", bound=CategoryOrm)
MODE = Literal['admin', 'user']


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = CategoryOrm

    def create_category(self, data: CategoryCreate) -> T:
        new_category = self.model(
            title=data.title,
            description=data.description,
            image_path=data.image_path if data.image_path else None,
            timestamp_add=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            timestamp_change=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.db.add(new_category)
        self.db.commit()
        self.db.refresh(new_category)
        return new_category

    def select_all_categories(self, mode: MODE) -> List[Type[T]]:
        if mode == "admin":
            return self.db.query(self.model).all()
        return self.db.query(self.model).filter(self.model.is_published).all()

    def select_category_by_id(self, category_id: int, mode: MODE) -> Union[T, None]:
        if mode == "admin":
            return self.db.query(self.model).filter(self.model.id == category_id).first()
        return self.db.query(self.model).filter(self.model.id == category_id).filter(self.model.is_published).first()

    def update_category(self, data:  CategoryUpdate, category_id: int) -> T:
        category = self.select_category_by_id(category_id=category_id, mode="admin")

        for key, value in data.dict().items():
            if value:
                setattr(category, key, value)

        category.timestamp_change = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.select_category_by_id(category_id=category_id, mode="admin")
        self.db.delete(category)
        self.db.commit()

    def publish_category(self, category_id: int) -> T:
        category = self.select_category_by_id(category_id=category_id, mode="admin")
        category.is_published = True
        category.timestamp_change = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.commit()
        self.db.refresh(category)
        return category

    def search_category(self, query: str) -> List[Type[T]]:
        regex_query = fr"\y{query}.*"
        return self.db.query(self.model).filter(self.model.title.op('~*')(regex_query)).all()
