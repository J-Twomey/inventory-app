from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from main import app
from src.database import (
    Base,
    get_db,
)


TEST_DATABASE_URL = 'sqlite:///:memory:'


@pytest.fixture(scope='session')
def engine() -> Generator[Engine, None, None]:
    engine = create_engine(TEST_DATABASE_URL, connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(engine: Engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as cl:
        yield cl
