from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import Token, UserCreate, UserRead
from app.security import (
    create_access_token,
    hash_password,
    verify_password,
)

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
    # Store a password hash rather than the original password.
    user = User(
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        # PostgreSQL code 23505 means a unique constraint was violated.
        # Check the constraint name to identify a duplicate email specifically.
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

    # Reload database-generated values; UserRead excludes the password hash.
    db.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # The login form calls this field "username"; our API uses it for email.
    email = form_data.username.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    # Use the same error for an unknown email and an incorrect password.
    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Return a signed token for authenticating subsequent API requests.
    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
    )