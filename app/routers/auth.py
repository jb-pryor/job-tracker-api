from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead
from app.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    user = User(
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if (
            getattr(error.orig, "sqlstate", None) == "23505"
            and getattr(
                getattr(error.orig, "diag", None),
                "constraint_name",
                None,
            ) == "users_email_key"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from error

        raise

    db.refresh(user)
    return user