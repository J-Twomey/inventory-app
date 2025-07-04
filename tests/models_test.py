import pytest

from sqlalchemy.orm import Session

import src.crud as crud
from .conftest import ItemFactory


@pytest.mark.parametrize(
    ('purchase_price', 'grading_fees', 'expected_total'),
    (
        pytest.param(10, {}, 10, id='no_grading_fees'),
        pytest.param(10, {1: 100}, 110, id='single_grading_fee'),
        pytest.param(10, {1: 100, 2: 200}, 310, id='multiple_grading_fees'),
    ),
)
def test_total_cost_python(
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        expected_total: int,
) -> None:
    item = item_factory.get(purchase_price=purchase_price, grading_fee=grading_fees)
    assert item.total_cost == expected_total


@pytest.mark.parametrize(
    ('purchase_price', 'grading_fees', 'expected_total'),
    (
        pytest.param(10, {}, 10, id='no_grading_fees'),
        pytest.param(10, {1: 100}, 110, id='single_grading_fee'),
        pytest.param(10, {1: 100, 2: 200}, 310, id='multiple_grading_fees'),
    ),
)
def test_total_cost_sql(
        db_session: Session,
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        expected_total: int,
) -> None:
    item = item_factory.get(purchase_price=purchase_price, grading_fee=grading_fees)
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.total_cost == expected_total
