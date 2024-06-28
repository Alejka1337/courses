from typing import List, Union

from sqlalchemy.orm import Session

from src.models import CategoryOrm
from src.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db
        self.model = CategoryOrm

    def create_category(self, data: CategoryCreate) -> CategoryOrm:
        new_category = self.model(
            title=data.title,
            description=data.description,
            image_path=data.image_path if data.image_path else None,
        )

        self.db.add(new_category)
        self.db.commit()
        self.db.refresh(new_category)
        return new_category

    def select_all_categories(self) -> Union[List[CategoryOrm], List]:
        return self.db.query(self.model).all()

    def select_category_by_id(self, category_id: int) -> Union[CategoryOrm, None]:
        return self.db.query(self.model).filter(self.model.id == category_id).first()

    def update_category(self, data:  CategoryUpdate, category_id: int) -> CategoryOrm:
        category = self.select_category_by_id(category_id=category_id)

        for key, value in data.dict().items():
            if value:
                setattr(category, key, value)

        self.db.commit()
        self.db.refresh(category)
        return category

    def delete_category(self, category_id: int) -> None:
        category = self.select_category_by_id(category_id=category_id)
        self.db.delete(category)
        self.db.commit()

    def search_category(self, query: str):
        regex_query = fr"\y{query}.*"
        return self.db.query(self.model).filter(self.model.title.op('~*')(regex_query)).all()
