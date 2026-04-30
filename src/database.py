import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    try:
        dev_mode = os.environ['DEV_MODE'] == '1'
    except KeyError:
        raise RuntimeError('DEV_MODE environment variable is not set') from None

    url = 'sqlite:///./db/test.db' if dev_mode else 'sqlite:///./db/prod_test.db'
    return create_engine(url, connect_args={'check_same_thread': False})


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    local_session = get_sessionmaker()
    db = local_session()
    try:
        yield db
    finally:
        db.close()
