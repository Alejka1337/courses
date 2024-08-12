from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.crud.category import CategoryRepository
from src.enums import StaticFileType
from src.models import UserOrm
from src.schemas.category import (CategoryCreate, CategoryUpdate, CategoryResponse,
                                  CategoryImagePathResponse, CategoryDeleteResponse)
from src.session import get_db
from src.utils.exceptions import PermissionDeniedException, CategoryNotFoundException
from src.utils.get_user import get_current_user
from src.utils.save_files import save_file

router = APIRouter(prefix="/category")


@router.post("/create", response_model=CategoryResponse)
async def create_category(
        data: CategoryCreate,
        user: UserOrm = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if user.is_moder:
        repository = CategoryRepository(db=db)
        return repository.create_category(data=data)
    else:
        raise PermissionDeniedException()


@router.get("/all", response_model=list[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    result = repository.select_all_categories()

    if not result:
        raise CategoryNotFoundException()
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db=db)
    result = repository.select_category_by_id(category_id=category_id)
    if not result:
        raise CategoryNotFoundException()
    return result


@router.put("/update/{category_id}", response_model=CategoryResponse)
async def update_category(
        data: CategoryUpdate,
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CategoryRepository(db=db)
        return repository.update_category(data=data, category_id=category_id)
    else:
        raise PermissionDeniedException()


@router.post("/upload/image", response_model=CategoryImagePathResponse)
async def upload_category_image(
        image: UploadFile = File(...),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        path = save_file(file=image, file_type=StaticFileType.category_avatar.value)
        return CategoryImagePathResponse(newPath=path)
    else:
        raise PermissionDeniedException()


@router.delete("/delete/{category_id}", response_model=CategoryDeleteResponse)
async def delete_category(
        category_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_moder:
        repository = CategoryRepository(db=db)
        repository.delete_category(category_id=category_id)
        return CategoryDeleteResponse()
    else:
        raise PermissionDeniedException()
