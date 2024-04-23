from typing import Union, List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Response
from sqlalchemy.orm import Session

from src.crud.category import (create_category_db, delete_category_db, select_all_categories_db,
                               select_category_by_id_db, update_category_db)
from src.enums import UserType
from src.models import UserOrm, CategoryOrm
from src.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from src.session import get_db
from src.utils.get_user import get_current_user
from src.utils.save_files import save_category_course_avatar

router = APIRouter(prefix="/category")


@router.post("/create", response_model=CategoryOut)
async def create_category(
        data: CategoryCreate,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Union[CategoryOrm, Response]:

    if user.usertype == UserType.moder.value:
        return create_category_db(db=db, data=data)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.get("/all")
async def get_categories(db: Session = Depends(get_db)):
    return select_all_categories_db(db=db)


@router.get("/{category_id}")
async def get_category(category_id: int, db: Session = Depends(get_db)):
    return select_category_by_id_db(db=db, category_id=category_id)


@router.put("/update/{category_id}")
async def update_category(
        data: CategoryUpdate,
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        return update_category_db(db=db, data=data, category_id=category_id)
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.post("/upload/image")
async def upload_category_image(
        image: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        path = save_category_course_avatar(image)
        return {"newPath": path}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")


@router.delete("/delete/{category_id}")
async def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        delete_category_db(db=db, category_id=category_id)
        return {"message": "Category have been deleted"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
