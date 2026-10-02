from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.database import get_db
from app.dependencies import get_current_user
from app.models import JobApplication, User
from app.schemas import (
    ApplicationCreate,
    ApplicationList,
    ApplicationRead,
    ApplicationStatus,
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


@router.get("", response_model=ApplicationList)
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: ApplicationStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    filters = [
        JobApplication.user_id == current_user.id,
    ]

    if status is not None:
        filters.append(JobApplication.status == status)

    total = db.scalar(
        select(func.count())
        .select_from(JobApplication)
        .where(*filters)
    )

    statement = (
        select(JobApplication)
        .where(*filters)
        .order_by(
            JobApplication.created_at.desc(),
            JobApplication.id.desc(),
        )
        .limit(limit)
        .offset(offset)
    )

    applications = db.scalars(statement).all()

    return ApplicationList(
        items=[
            ApplicationRead.model_validate(application)
            for application in applications
        ],
        total=total,
        limit=limit,
        offset=offset,
    )

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


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_application(
    application_id: int,
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

    db.delete(application)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return Response(status_code=status.HTTP_204_NO_CONTENT)