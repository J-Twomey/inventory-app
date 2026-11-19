import pytest

from src import (
    item_enums,
    state_rules,
)

from .conftest import ItemFactory


def test_get_item_status_change_after_record_delete_submitted_item_returns_storage(
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(status=item_enums.Status.SUBMITTED)

    new_status = state_rules.get_item_status_change_after_record_delete(item)

    assert new_status == item_enums.Status.STORAGE


@pytest.mark.parametrize(
    'status',
    [
        pytest.param(item_enums.Status.STORAGE, id='storage'),
        pytest.param(item_enums.Status.VAULT, id='vault'),
        pytest.param(item_enums.Status.ORDER, id='order'),
        pytest.param(item_enums.Status.LISTED, id='listed'),
        pytest.param(item_enums.Status.CLOSED, id='closed'),
    ],
)
def test_get_item_status_change_after_record_delete_non_submitted_item_returns_none(
    item_factory: ItemFactory,
    status: item_enums.Status,
) -> None:
    item = item_factory.get(status=status)

    assert state_rules.get_item_status_change_after_record_delete(item) is None
