import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app

test_database_url = os.getenv("TEST_DATABASE_URL")

if not test_database_url:
    raise RuntimeError("TEST_DATABASE_URL is not set.")

if make_url(test_database_url).database != "job_tracker_test":
    raise RuntimeError("Tests must use the job_tracker_test database.")

test_engine = create_engine(test_database_url, pool_pre_ping=True)


@pytest.fixture
def db_session():
    with test_engine.connect() as connection:
        transaction = connection.begin()

        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
        ) as session:
            try:
                yield session
            finally:
                transaction.rollback()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)