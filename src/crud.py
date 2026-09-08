from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from sqlalchemy import (
    and_,
    desc,
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from .item_enums import (
    GradingCompany,
    Intent,
    Qualifier,
    Status,
)
from .models import (
    GradingRecord,
    Item,
    Refund,
    Remuneration,
    Submission,
)
from .schemas import (
    GradingRecordCreate,
    GradingRecordUpdate,
    ItemCreate,
    ItemSearch,
    ItemUpdate,
    RefundCreate,
    RefundUpdate,
    RemunerationCreate,
    RemunerationUpdate,
    SubmissionCreate,
)
from .validators import (
    check_intent,
    check_item_can_return_to_submitted,
    check_item_valid_after_update,
    check_new_item_not_submitted,
    check_no_duplicate_items_in_submission,
    check_required_fields_not_removed,
    check_status,
    check_status_change_to_submitted_valid,
    check_valid_grading_record_update,
    check_valid_intent_or_status_update,
    check_valid_submission_field_update,
)


def create_item(
    db: Session,
    item: ItemCreate,
) -> Item:
    check_new_item_not_submitted(item)
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

    if len(post_filters) > 0:
        results = [item for item in results if all(keep(item) for keep in post_filters)]
    return results


def qualifiers_filter(qualifiers: list[Qualifier]) -> Callable[[Item], bool]:
    return lambda item: all(q in item.qualifiers for q in qualifiers)


def build_search_filters(
    search_params: dict[str, Any],
) -> tuple[list[ColumnElement[bool]], list[Callable[[Item], bool]]]:
    filters: list[ColumnElement[bool]] = []
    post_filters: list[Callable[[Item], bool]] = []
    for field, value in search_params.items():
        if value is None or value == []:
            continue

        if field == 'qualifiers':
            post_filters.append(qualifiers_filter(value))
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
    check_required_fields_not_removed(item_update, ItemCreate)
    check_valid_intent_or_status_update(
        Intent(item.intent),
        Status(item.status),
        item_update.intent,
        item_update.status,
    )
    if item_update.status == Status.SUBMITTED:
        check_status_change_to_submitted_valid(item)
    check_item_valid_after_update(item, item_update)
    perform_item_update(item, item_update)
    db.commit()
    db.refresh(item)
    return 303


def perform_item_update(
    item: Item,
    item_update: ItemUpdate,
) -> None:
    update_data = item_update.to_model_kwargs()
    for key, value in update_data.items():
        setattr(item, key, value)


def create_submission(
    db: Session,
    submission_summary: SubmissionCreate,
    item_ids: list[int],
) -> None:
    check_no_duplicate_items_in_submission(item_ids)
    linked_items: list[Item] = []
    for item_id in item_ids:
        linked_item = get_item(db, item_id)
        if linked_item is None:
            raise ValueError(f'Item with id {item_id} not found')
        check_intent(linked_item, desired=Intent.GRADE)
        check_status(linked_item, desired=Status.STORAGE)
        linked_items.append(linked_item)

    try:
        submission_summary_data = submission_summary.to_model_kwargs()
        submission = Submission(**submission_summary_data)
        db.add(submission)
        db.flush()
        grading_records = [
            GradingRecordCreate(
                item_id=i,
                submission_id=submission.id,
            )
            for i in item_ids
        ]

        for grading_record, linked_item in zip(grading_records, linked_items, strict=True):
            db.add(GradingRecord(**grading_record.to_model_kwargs()))

            # Update item to SUBMITTED
            item_update = ItemUpdate(status=Status.SUBMITTED)
            perform_item_update(linked_item, item_update)

        db.commit()
    except IntegrityError:
        db.rollback()
        raise SubmissionNumberConflictError from None
    except Exception:
        db.rollback()
        raise


def get_submission(
    db: Session,
    submission_id: int,
) -> Submission | None:
    return db.query(Submission).filter(Submission.id == submission_id).first()


def get_newest_submissions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Submission]:
    submissions = (
        db.query(
            Submission,
        )
        .order_by(Submission.submission_number.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return list(reversed(submissions))


def get_total_number_of_submissions(db: Session) -> int:
    return db.query(Submission).count()


class SubmissionNotFoundError(Exception):
    pass


class SubmissionNumberConflictError(Exception):
    pass


def edit_submission_single_field(
    db: Session,
    submission_id: int,
    field: str,
    update_value: date | int | GradingCompany | None,
) -> None:
    submission = get_submission(db, submission_id)
    if submission is None:
        raise SubmissionNotFoundError
    check_valid_submission_field_update(submission, field, update_value)
    try:
        setattr(submission, field, update_value)
        db.commit()
        db.refresh(submission)
    except IntegrityError:
        db.rollback()
        raise SubmissionNumberConflictError from None


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
    items = (
        db.query(GradingRecord)
        .order_by(
            desc(GradingRecord.submission_number),
            desc(GradingRecord.id),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return list(reversed(items))


def get_total_number_of_grading_records(db: Session) -> int:
    return db.query(GradingRecord).count()


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

    if all(getattr(linked_item, f) is None for f in Status.STORAGE.required_to_be_null):
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


def get_item_status_after_record_edit(
    record: GradingRecord,
    update_data: dict[str, Any],
) -> Status | None:
    """The item's status follows its record closing (returned from grading) or re-opening"""
    if record.grade is None and update_data.get('grade') is not None:
        return Status.STORAGE
    grade_removed = (
        record.grade is not None and 'grade' in update_data and update_data['grade'] is None
    )
    if grade_removed and not update_data.get('is_cracked', record.is_cracked):
        return Status.SUBMITTED
    return None


def edit_grading_record(
    db: Session,
    record_id: int,
    record_update: GradingRecordUpdate,
) -> int:
    record = get_grading_record(db, record_id)
    if record is None:
        return 404
    check_valid_grading_record_update(record, record_update)

    update_data = record_update.to_model_kwargs()
    new_status = get_item_status_after_record_edit(record, update_data)
    if new_status is not None:
        linked_item = get_item(db, record.item_id)
        if linked_item is None:
            raise ValueError(f'Linked item not found for item #{record.item_id}')
        if new_status == Status.SUBMITTED:
            check_item_can_return_to_submitted(linked_item)
        perform_item_update(linked_item, ItemUpdate(status=new_status))

    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return 303


def get_max_sub_number(db: Session) -> int:
    return db.scalar(select(func.max(Submission.submission_number))) or 0


def create_refund(
    db: Session,
    refund: RefundCreate,
) -> Refund:
    db_refund = Refund(**refund.to_model_kwargs())
    db.add(db_refund)
    db.commit()
    db.refresh(db_refund)
    return db_refund


def get_newest_refunds(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Refund]:
    refunds = (
        db.query(Refund)
        .order_by(
            desc(Refund.refund_date),
            desc(Refund.id),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return list(reversed(refunds))


def get_total_number_of_refunds(db: Session) -> int:
    return db.query(Refund).count()


def get_refund(
    db: Session,
    refund_id: int,
) -> Refund | None:
    return db.query(Refund).filter(Refund.id == refund_id).first()


def delete_refund_by_id(
    db: Session,
    refund_id: int,
) -> bool:
    refund = get_refund(db, refund_id)
    if refund is None:
        return False
    db.delete(refund)
    db.commit()
    return True


def edit_refund(
    db: Session,
    refund_id: int,
    refund_update: RefundUpdate,
) -> int:
    refund = get_refund(db, refund_id)
    if refund is None:
        return 404
    check_required_fields_not_removed(refund_update, RefundCreate)
    perform_refund_update(refund, refund_update)
    db.commit()
    db.refresh(refund)
    return 303


def perform_refund_update(
    refund: Refund,
    refund_update: RefundUpdate,
) -> None:
    for key, value in refund_update.to_model_kwargs().items():
        setattr(refund, key, value)


def create_remuneration(
    db: Session,
    remuneration: RemunerationCreate,
) -> Remuneration:
    db_remuneration = Remuneration(**remuneration.to_model_kwargs())
    db.add(db_remuneration)
    db.commit()
    db.refresh(db_remuneration)
    return db_remuneration


def get_newest_remunerations(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Remuneration]:
    remunerations = (
        db.query(Remuneration)
        .order_by(
            desc(Remuneration.remuneration_date),
            desc(Remuneration.id),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return list(reversed(remunerations))


def get_total_number_of_remunerations(db: Session) -> int:
    return db.query(Remuneration).count()


def get_remuneration(
    db: Session,
    remuneration_id: int,
) -> Remuneration | None:
    return db.query(Remuneration).filter(Remuneration.id == remuneration_id).first()


def delete_remuneration_by_id(
    db: Session,
    remuneration_id: int,
) -> bool:
    remuneration = get_remuneration(db, remuneration_id)
    if remuneration is None:
        return False
    db.delete(remuneration)
    db.commit()
    return True


def edit_remuneration(
    db: Session,
    remuneration_id: int,
    remuneration_update: RemunerationUpdate,
) -> int:
    remuneration = get_remuneration(db, remuneration_id)
    if remuneration is None:
        return 404
    check_required_fields_not_removed(remuneration_update, RemunerationCreate)
    perform_remuneration_update(remuneration, remuneration_update)
    db.commit()
    db.refresh(remuneration)
    return 303


def perform_remuneration_update(
    remuneration: Remuneration,
    remuneration_update: RemunerationUpdate,
) -> None:
    for key, value in remuneration_update.to_model_kwargs().items():
        setattr(remuneration, key, value)
