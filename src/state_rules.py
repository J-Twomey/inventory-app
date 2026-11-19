from typing import Any

from .item_enums import (
    Intent,
    Status,
)
from .models import (
    GradingRecord,
    Item,
)


def get_item_status_change_after_record_edit(
    record: GradingRecord,
    update_data: dict[str, Any],
) -> Status | None:
    """The item's status follows its record closing (returned from grading) or re-opening.

    Returns None if the edit doesn't change the item's status.
    """
    # Adding a grade -> return from submission -> status is STORAGE
    if update_is_adding_grade(record, update_data):
        return Status.STORAGE

    # isn't cracked + has no grade -> status is SUBMITTED
    if update_is_removing_grade_from_non_cracked_record(record, update_data):
        return Status.SUBMITTED

    # No change
    return None


def get_item_status_change_after_record_delete(item: Item) -> Status | None:
    """A SUBMITTED item goes back to STORAGE once a grading record is deleted.

    Returns None if the deletion doesn't change the item's status.
    """
    if item.status == Status.SUBMITTED:
        return Status.STORAGE
    return None


def get_item_intent_change_after_record_edit(
    record: GradingRecord,
    update_data: dict[str, Any],
    item: Item,
) -> Intent | None:
    """Returns None if the edit doesn't change the item's intent."""
    # Adding a grade -> return from submission -> default to KEEP
    if update_is_adding_grade(record, update_data):
        return Intent.KEEP

    # Removing grade from record that isn't cracked -> not returned from submission -> intent GRADE
    if update_is_removing_grade_from_non_cracked_record(record, update_data):
        return Intent.GRADE

    # is_cracked=False and item graded -> in possession -> default to KEEP
    if (
        update_is_setting_is_cracked_to_false_on_graded_record(record, update_data)
        and item.intent == Intent.GRADE
    ):
        return Intent.KEEP

    # No change
    return None


def update_is_adding_grade(record: GradingRecord, update_data: dict[str, Any]) -> bool:
    return record.grade is None and update_data.get('grade') is not None


def update_is_removing_grade_from_non_cracked_record(
    record: GradingRecord,
    update_data: dict[str, Any],
) -> bool:
    # Is the update removing the grade from the record
    grade_removed = (
        record.grade is not None and 'grade' in update_data and update_data['grade'] is None
    )
    # Is the record cracked after the update is performed
    is_cracked_after_update = update_data.get('is_cracked', record.is_cracked)

    # True if and only if a grade is removed from a record that hasn't been cracked
    return grade_removed and not is_cracked_after_update


def update_is_setting_is_cracked_to_false_on_graded_record(
    record: GradingRecord,
    update_data: dict[str, Any],
) -> bool:
    currently_cracked = record.is_cracked
    update_assigns_is_cracked_to_false = update_data.get('is_cracked') is False
    record_still_has_grade_after_update = update_data.get('grade', record.grade) is not None
    return (
        currently_cracked
        and update_assigns_is_cracked_to_false
        and record_still_has_grade_after_update
    )
