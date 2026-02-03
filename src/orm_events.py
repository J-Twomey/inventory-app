from collections.abc import Iterable
from typing import Protocol

from sqlalchemy import event
from sqlalchemy.engine import Engine

from src.models import (
    GradingRecord,
    Submission,
)
from sqlalchemy.orm import Session
from sqlalchemy.pool import ConnectionPoolEntry


class SQLiteCursor(Protocol):
    def execute(self, sql: str) -> None: ...
    def close(self) -> None: ...


class SQLiteDBAPIConnection(Protocol):
    def cursor(self) -> SQLiteCursor: ...


class FlushContext(Protocol):
    '''No typing required'''
    pass


@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(
    dbapi_connection: SQLiteDBAPIConnection,
    connection_record: ConnectionPoolEntry,
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


@event.listens_for(Session, 'before_flush')
def delete_empty_submissions(
    session: Session,
    flush_context: FlushContext,
    instances: Iterable[object] | None,
) -> None:
    affected_submissions: set[Submission] = set()

    for obj in session.deleted:
        if isinstance(obj, GradingRecord):
            if obj.submission is not None:
                affected_submissions.add(obj.submission)

    for submission in affected_submissions:
        remaining = [
            gr
            for gr in submission.submission_items
            if gr not in session.deleted
        ]

        if not remaining:
            session.delete(submission)
