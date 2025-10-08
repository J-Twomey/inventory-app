from collections.abc import Sequence
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
    Item,
    ItemSubmission,
    Submission,
)
from .schemas import (
    ItemCreate,
    ItemSearch,
    ItemUpdate,
    ItemSubmissionCreate,
    ItemSubmissionUpdate,
    SubmissionCreate,
)
from .validators import (
    check_intent,
    check_status,
)


import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    filename='log.log',
    filemode='a'
)
logger = logging.getLogger(__name__)


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


def delete_item_by_id(
        db: Session,
        item_id: int,
) -> bool:
    item = get_item(db, item_id)
    if item is None:
        return False
    # Delete all submissions associated with this item (if any)
    submissions = get_all_submissions_for_item(db, item_id)
    for submission in submissions:
        perform_delete_submission_item(db, submission)
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

    # Post filtering (for qualifiers)
    for field, value in post_filters:
        if field == 'qualifiers':
            qualifier_values = [q for q in value]
            results = [
                item for item in results
                if all(q in item.qualifiers for q in qualifier_values)
            ]
    return results


def edit_item(
        db: Session,
        item_id: int,
        item_update: ItemUpdate,
) -> int:
    item = get_item(db, item_id)
    if item is None:
        return 404
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


def build_search_filters(
        search_params: dict[str, Any],
) -> tuple[list[BinaryExpression[Any]], list[tuple[str, Any]]]:
    filters: list[BinaryExpression[Any]] = []
    post_filters: list[tuple[str, Any]] = []
    for field, value in search_params.items():
        if value is None or value == []:
            continue

        # Filter qualifiers and cracked_from after the sql search
        if field in ['qualifiers', 'cracked_from']:
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


def create_submission(
        db: Session,
        submission_summary: SubmissionCreate,
        submission_items: list[ItemSubmissionCreate],
) -> None:
    try:
        submission_summary_data = submission_summary.to_model_kwargs()
        db.add(Submission(**submission_summary_data))

        for submission_data in submission_items:
            submission_item = ItemSubmission(**submission_data.to_model_kwargs())
            linked_item = get_item(db, submission_item.item_id)
            if linked_item is None:
                raise ValueError(f'Item with id {submission_item.item_id} not found')
            check_intent(linked_item, desired=Intent.GRADE)
            check_status(linked_item, desired=Status.STORAGE)
            db.add(submission_item)

            # Update item to be SUBMITTED
            item_update = ItemUpdate(status=Status.SUBMITTED)
            perform_item_update(linked_item, item_update)

        db.commit()
    except Exception:
        db.rollback()
        raise


def get_newest_submissions(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> Sequence[Submission]:
    submissions = db.query(
        Submission,
    ).order_by(Submission.submission_number.desc()).offset(skip).limit(limit).all()
    return list(reversed(submissions))


def get_submission_item(
        db: Session,
        submission_id: int,
) -> ItemSubmission | None:
    return db.query(ItemSubmission).filter(ItemSubmission.id == submission_id).first()


def get_all_submissions_for_item(
        db: Session,
        item_id: int,
) -> list[ItemSubmission]:
    return db.query(ItemSubmission).filter(ItemSubmission.item_id == item_id).all()


def get_newest_submission_items(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> Sequence[ItemSubmission]:
    items = db.query(
        ItemSubmission,
    ).order_by(ItemSubmission.id.desc()).offset(skip).limit(limit).all()
    return list(reversed(items))


def delete_submission_item_by_id(
        db: Session,
        submission_id: int,
) -> bool:
    submission = get_submission_item(db, submission_id)
    if submission is None:
        return False

    linked_item = get_item(db, submission.item_id)
    if linked_item is None:
        raise ValueError(f'Item with id {submission.item_id} not found')

    # Return item status to STORAGE
    item_update = ItemUpdate(status=Status.STORAGE)
    perform_item_update(linked_item, item_update)
    perform_delete_submission_item(db, submission)
    db.commit()
    return True


def perform_delete_submission_item(
        db: Session,
        submission: ItemSubmission,
) -> None:
    db.delete(submission)


def edit_submission_item(
        db: Session,
        submission_id: int,
        submission_update: ItemSubmissionUpdate,
) -> int:
    submission = get_submission_item(db, submission_id)
    if submission is None:
        return 404

    update_data = submission_update.to_model_kwargs()

    for key, value in update_data.items():
        setattr(submission, key, value)

    db.commit()
    db.refresh(submission)
    return 303
