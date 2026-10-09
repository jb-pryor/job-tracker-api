import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Load .env from the project's root directory.
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

# Manage database connections and check pooled connections before using them.
engine = create_engine(database_url, pool_pre_ping=True)

# Create sessions bound to this engine.
SessionLocal = sessionmaker(
    bind=engine,
    # Queries won't automatically send pending changes to the database.
    autoflush=False,
    # Keep loaded attributes available after committing.
    expire_on_commit=False,
)


# Models inherit from Base; its metadata tracks their table definitions for Alembic.
class Base(DeclarativeBase):
    pass


def get_db():
    # Give the endpoint a session and close it when the request finishes.
    with SessionLocal() as session:
        yield session