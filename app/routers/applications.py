from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models import JobApplication, User
from app.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)

router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = JobApplication(
        user_id=current_user.id,
        company=application_data.company,
        job_title=application_data.job_title,
        status=application_data.status,
        job_url=(
            str(application_data.job_url)
            if application_data.job_url is not None
            else None
        ),
        notes=application_data.notes,
        applied_on=application_data.applied_on,
    )

    db.add(application)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(JobApplication)
        .where(JobApplication.user_id == current_user.id)
        .order_by(
            JobApplication.created_at.desc(),
            JobApplication.id.desc(),
        )
    )

    applications = db.scalars(statement).all()
    return applications

@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(JobApplication).where(
        JobApplication.id == application_id,
        JobApplication.user_id == current_user.id,
    )

    application = db.scalar(statement)

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    return application


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    application_data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.scalar(
        select(JobApplication).where(
            JobApplication.id == application_id,
            JobApplication.user_id == current_user.id,
        )
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )

    updates = application_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field == "job_url" and value is not None:
            value = str(value)

        setattr(application, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)
    return application