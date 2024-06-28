from typing import Union

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from src.crud.category import CategoryRepository
from src.enums import StaticFileType, UserType
from src.models import CategoryOrm, UserOrm
from src.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/category")


@router.post("/create", response_model=CategoryOut)
async def create_category(
        data: CategoryCreate,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Union[CategoryOrm, Response]:

    if user.usertype == UserType.moder.value:
        repository = CategoryRepository(db=db)
        return repository.create_category(data=data)
    else:
        raise PermissionDeniedException()


@router.get("/all")
async def get_categories(db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    return repository.select_all_categories()


@router.get("/{category_id}")
async def get_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    return repository.select_category_by_id(category_id=category_id)


@router.put("/update/{category_id}")
async def update_category(
        data: CategoryUpdate,
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CategoryRepository(db=db)
        return repository.update_category(data=data, category_id=category_id)
    else:
        raise PermissionDeniedException()


@router.post("/upload/image")
async def upload_category_image(
        image: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        path = save_file(file=image, file_type=StaticFileType.category_avatar.value)
        return {"newPath": path}
    else:
        raise PermissionDeniedException()


@router.delete("/delete/{category_id}")
async def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.usertype == UserType.moder.value:
        repository = CategoryRepository(db=db)
        repository.delete_category(category_id=category_id)
        return {"message": "Category have been deleted"}
    else:
        raise PermissionDeniedException()
