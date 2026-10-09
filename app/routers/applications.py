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

# All routes below start with /applications and share a section in the docs.
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
    # Assign ownership using the authenticated user, rather than a submitted user ID.
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

    # Commit saves the transaction; rollback resets it if saving fails.
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # Reload database-generated values, such as the ID and timestamps.
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
    # Every list query is restricted to the authenticated user's applications.
    filters = [
        JobApplication.user_id == current_user.id,
    ]

    if status is not None:
        filters.append(JobApplication.status == status)

    # Count all matching applications before applying pagination.
    total = db.scalar(
        select(func.count())
        .select_from(JobApplication)
        .where(*filters)
    )

    # Return newest first, using the ID to break ties between timestamps.
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

    # Convert database objects into response schemas and include pagination details.
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
    # Match both the application ID and owner so other users cannot access it.
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

    # PATCH changes only submitted fields, including explicitly submitted nulls.
    updates = application_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        # Convert Pydantic URL values to strings for database storage.
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

    # A successful deletion returns 204 with no response body.
    return Response(status_code=status.HTTP_204_NO_CONTENT)