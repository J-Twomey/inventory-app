import pytest

import src.validators as validators
from src.schemas import GradingRecordUpdate
from .conftest import GradingRecordFactory


def test_check_valid_grading_record_update_already_graded(
        grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=1000, grade=9., cert=10000)
    update = GradingRecordUpdate()
    validators.check_valid_grading_record_update(record, update)


def test_check_valid_grading_record_update_changes_ok(
        grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=None, grade=None, cert=None)
    update = GradingRecordUpdate(grading_fee=100, grade=9.5, cert=12345)
    validators.check_valid_grading_record_update(record, update)


def test_check_valid_grading_record_update_changes_ng(
        grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=None, grade=None, cert=None)
    update = GradingRecordUpdate(grading_fee=100, grade=9.5, cert=None)
    with pytest.raises(
        ValueError,
        match=(
            'Updating a record from graded to graded requires setting all of grading_fee, '
            'grade, and cert'
        ),
    ):
        validators.check_valid_grading_record_update(record, update)
