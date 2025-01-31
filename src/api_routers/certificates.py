from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.crud.certificate import CertificateRepository
from src.session import get_db
from src.utils.get_user import get_current_user
from src.models import UserOrm
from src.utils.exceptions import PermissionDeniedException


router = APIRouter(prefix="/certificates")


@router.get("/my")
async def get_my_certificates(
        student_id: int,
        db: Session = Depends(get_db),
        user: UserOrm = Depends(get_current_user)
):
    if user.is_student:
        repository = CertificateRepository(db=db)
        return {
            "certificates": repository.select_student_certificate(student_id=student_id)
        }

    raise PermissionDeniedException()
