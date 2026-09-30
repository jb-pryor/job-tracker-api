from fastapi import Depends, FastAPI

from app.dependencies import get_current_user
from app.models import User
from app.routers.auth import router as auth_router
from app.schemas import UserRead

app = FastAPI(title="Job Tracker API")

app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user