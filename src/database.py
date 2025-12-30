from typing import (
    Generator,
    Protocol,
)

from sqlalchemy import (
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)
from sqlalchemy.pool import ConnectionPoolEntry


SQLALCHEMY_DATABASE_URL = 'sqlite:///./db/test6.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SQLiteCursor(Protocol):
    def execute(self, sql: str) -> None: ...
    def close(self) -> None: ...


class SQLiteDBAPIConnection(Protocol):
    def cursor(self) -> SQLiteCursor: ...


@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(
        dbapi_connection: SQLiteDBAPIConnection,
        connection_record: ConnectionPoolEntry,
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()
