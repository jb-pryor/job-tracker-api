from fastapi import Depends, FastAPI

from app.dependencies import get_current_user
from app.models import User
from app.routers.auth import router as auth_router
from app.schemas import UserRead

from app.routers.applications import router as applications_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Job Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_router)

app.include_router(applications_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/users/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user