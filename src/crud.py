from collections.abc import Sequence
from datetime import date
from typing import Any

from sqlalchemy import (
    and_,
    select,
)
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import BinaryExpression

from .item_enums import (
    Intent,
    Status,
)
from .models import (
    GradingRecord,
    Item,
    Submission,
)
from .schemas import (
    GradingRecordCreate,
    GradingRecordUpdate,
    ItemCreate,
    ItemSearch,
    ItemUpdate,
    SubmissionCreate,
)
from .validators import (
    check_intent,
    check_status,
    check_valid_grading_record_update,
    check_valid_intent_or_status_update,
)


def create_item(
        db: Session,
        item: ItemCreate,
) -> Item:
    item_data = item.to_model_kwargs(
        exclude={
            'total_cost',
            'total_fees',
            'return_usd',
            'return_jpy',
            'net_jpy',
            'net_percent',
        },
    )
    db_item = Item(**item_data)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(
        db: Session,
        item_id: int,
) -> Item | None:
    return db.query(Item).filter(Item.id == item_id).first()


def get_newest_items(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> Sequence[Item]:
    items = db.query(Item).order_by(Item.id.desc()).offset(skip).limit(limit).all()
    return list(reversed(items))


def get_total_number_of_items(db: Session) -> int:
    return db.query(Item).count()


def delete_item_by_id(
        db: Session,
        item_id: int,
) -> bool:
    item = get_item(db, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def search_for_items(
        db: Session,
        search_params: ItemSearch,
) -> Sequence[Item]:
    search_values = search_params.model_dump(exclude_unset=True)
    filters, post_filters = build_search_filters(search_values)
    statement = select(Item)
    if len(filters) > 0:
        statement = statement.where(and_(*filters))
    results = db.execute(statement).scalars().all()

    # Post filtering (for qualifiers and grading_company)
    for field, value in post_filters:
        if field == 'qualifiers':
            qualifier_values = [q for q in value]
            results = [
                item for item in results
                if all(q in item.qualifiers for q in qualifier_values)
            ]
        elif field == 'grading_company':
            results = [item for item in results if item.grading_company == value]
    return results


def build_search_filters(
        search_params: dict[str, Any],
) -> tuple[list[BinaryExpression[Any]], list[tuple[str, Any]]]:
    filters: list[BinaryExpression[Any]] = []
    post_filters: list[tuple[str, Any]] = []
    for field, value in search_params.items():
        if value is None or value == []:
            continue

        # Filter qualifiers and cracked_from after the sql search
        if field in ['qualifiers', 'cracked_from', 'grading_company']:
            post_filters.append((field, value))
        elif field == 'submission_number':
            raise NotImplementedError
        elif field.endswith('_min'):
            base_field = field.removesuffix('_min')
            column = getattr(Item, base_field)
            filters.append(column >= value)
        elif field.endswith('_max'):
            base_field = field.removesuffix('_max')
            column = getattr(Item, base_field)
            filters.append(column <= value)
        else:
            column = getattr(Item, field)
            filters.append(column == value)
    return filters, post_filters


def edit_item(
        db: Session,
        item_id: int,
        item_update: ItemUpdate,
) -> int:
    item = get_item(db, item_id)
    if item is None:
        return 404
    check_valid_intent_or_status_update(
        Intent(item.intent),
        Status(item.status),
        item_update.intent,
        item_update.status,
    )
    perform_item_update(item, item_update)
    db.commit()
    db.refresh(item)
    return 303


def perform_item_update(
        item: Item,
        item_update: ItemUpdate,
) -> None:
    update_data = item_update.to_model_kwargs()
    # always add qualifiers even if it is an empty list
    update_data['qualifiers'] = item_update.qualifiers

    for key, value in update_data.items():
        setattr(item, key, value)


def create_submission(
        db: Session,
        submission_summary: SubmissionCreate,
        grading_records: list[GradingRecordCreate],
) -> None:
    try:
        submission_summary_data = submission_summary.to_model_kwargs()
        db.add(Submission(**submission_summary_data))

        for grading_record in grading_records:
            record = GradingRecord(**grading_record.to_model_kwargs())
            linked_item = get_item(db, record.item_id)
            if linked_item is None:
                raise ValueError(f'Item with id {record.item_id} not found')
            check_intent(linked_item, desired=Intent.GRADE)
            check_status(linked_item, desired=Status.STORAGE)
            db.add(record)

            # Update item to SUBMITTED
            item_update = ItemUpdate(status=Status.SUBMITTED)
            perform_item_update(linked_item, item_update)

        db.commit()
    except Exception:
        db.rollback()
        raise


def get_submission(
        db: Session,
        submission_number: int,
) -> Submission | None:
    return db.query(Submission).filter(Submission.submission_number == submission_number).first()


def get_newest_submissions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> list[Submission]:
    submissions = db.query(
        Submission,
    ).order_by(Submission.submission_number.desc()).offset(skip).limit(limit).all()
    return list(reversed(submissions))


def edit_submission_single_field(
        db: Session,
        submission_number: int,
        field: str,
        update_value: date | None,
) -> int:
    submission = get_submission(db, submission_number)
    if submission is None:
        return 404
    setattr(submission, field, update_value)
    db.commit()
    db.refresh(submission)
    return 303


def get_grading_record(
        db: Session,
        record_id: int,
) -> GradingRecord | None:
    return db.query(GradingRecord).filter(GradingRecord.id == record_id).first()


def get_all_grading_records_for_item(
        db: Session,
        item_id: int,
) -> list[GradingRecord]:
    return db.query(GradingRecord).filter(GradingRecord.item_id == item_id).all()


def get_newest_grading_records(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> Sequence[GradingRecord]:
    items = db.query(
        GradingRecord,
    ).order_by(GradingRecord.id.desc()).offset(skip).limit(limit).all()
    return list(reversed(items))


def delete_grading_record_by_id(
        db: Session,
        record_id: int,
) -> bool:
    record = get_grading_record(db, record_id)
    if record is None:
        return False

    linked_item = get_item(db, record.item_id)
    if linked_item is None:
        raise ValueError(f'Item with id {record.item_id} not found')

    # Return item status to STORAGE
    item_update = ItemUpdate(status=Status.STORAGE)
    perform_item_update(linked_item, item_update)
    perform_delete_grading_record(db, record)
    db.commit()
    return True


def perform_delete_grading_record(
        db: Session,
        record: GradingRecord,
) -> None:
    db.delete(record)


def edit_grading_record(
        db: Session,
        record_id: int,
        record_update: GradingRecordUpdate,
) -> int:
    record = get_grading_record(db, record_id)
    if record is None:
        return 404
    check_valid_grading_record_update(record, record_update)

    # Item is returning from being submitted so update status
    if record.grade is None and record_update.grade is not None:
        linked_item = get_item(db, record.item_id)
        if linked_item is not None:
            item_update = ItemUpdate(status=Status.STORAGE)
            perform_item_update(linked_item, item_update)
        else:
            raise ValueError(f'Linked item not found for item #{record.item_id}')

    update_data = record_update.to_model_kwargs()
    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return 303
