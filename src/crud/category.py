from typing import List, Union
from sqlalchemy.orm import Session

from src.models import CategoryOrm
from src.schemas.category import CategoryCreate, CategoryUpdate


def create_category_db(db: Session, data: CategoryCreate) -> CategoryOrm:
    new_category = CategoryOrm(
        title=data.title,
        description=data.description,
        image_path=data.image_path if data.image_path else None)

    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def select_all_categories_db(db: Session) -> Union[List[CategoryOrm], List]:
    return db.query(CategoryOrm).all()


def select_category_by_id_db(db: Session, category_id: int) -> Union[CategoryOrm, None]:
    return db.query(CategoryOrm).filter(CategoryOrm.id == category_id).first()


def update_category_db(db: Session, data:  CategoryUpdate, category_id: int) -> CategoryOrm:
    category = select_category_by_id_db(db=db, category_id=category_id)

    for key, value in data.dict().items():
        if value:
            setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category_db(db: Session, category_id: int) -> None:
    category = select_category_by_id_db(db=db, category_id=category_id)
    db.delete(category)
    db.commit()
