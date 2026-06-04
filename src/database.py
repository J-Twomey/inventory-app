import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import (
    create_engine,
    inspect,
)
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

    url = 'sqlite:///./db/dev.db' if dev_mode else 'sqlite:///./db/prod.db'
    return create_engine(url, connect_args={'check_same_thread': False})


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        cols = {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}
        return f'{self.__class__.__name__}({cols})'


def get_db() -> Generator[Session, None, None]:
    local_session = get_sessionmaker()
    db = local_session()
    try:
        yield db
    finally:
        db.close()
