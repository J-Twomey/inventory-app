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


@pytest.mark.parametrize(
    ('shipping', 'sale_fee', 'expected_total'),
    (
        pytest.param(None, None, None, id='no_fees'),
        pytest.param(None, 8.7, None, id='no_shipping'),
        pytest.param(5.5, None, None, id='no_sale_fee'),
        pytest.param(5.5, 8.7, 14.2, id='with_fees'),
    ),
)
def test_total_fees_python(
        item_factory: ItemFactory,
        shipping: float | None,
        sale_fee: float | None,
        expected_total: float | None,
) -> None:
    item = item_factory.get(shipping=shipping, sale_fee=sale_fee)
    assert item.total_fees == expected_total


@pytest.mark.parametrize(
    ('shipping', 'sale_fee', 'expected_total'),
    (
        pytest.param(None, None, None, id='no_fees'),
        pytest.param(None, 8.7, None, id='no_shipping'),
        pytest.param(5.5, None, None, id='no_sale_fee'),
        pytest.param(5.5, 8.7, 14.2, id='with_fees'),
    ),
)
def test_total_fees_sql(
        db_session: Session,
        item_factory: ItemFactory,
        shipping: float | None,
        sale_fee: float | None,
        expected_total: float | None,
) -> None:
    item = item_factory.get(shipping=shipping, sale_fee=sale_fee)
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.total_fees == expected_total


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'expected_return'),
    (
        pytest.param(None, None, None, None, id='no_fees'),
        pytest.param(None, 5.34, 8.66, None, id='no_sale_total'),
        pytest.param(11.23, None, 8.66, None, id='no_total_fee'),
        pytest.param(15.31, 5.54, 8.66, 1.11, id='net_positive'),
        pytest.param(10.35, 5.54, 8.66, -3.85, id='net_negative'),
    ),
)
def test_return_usd_python(
        item_factory: ItemFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        expected_return: float | None,
) -> None:
    item = item_factory.get(sale_total=sale_total, shipping=shipping, sale_fee=sale_fee)
    assert item.return_usd == expected_return


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'expected_return'),
    (
        pytest.param(None, None, None, None, id='no_fees'),
        pytest.param(None, 5.34, 8.66, None, id='no_sale_total'),
        pytest.param(11.23, None, 8.66, None, id='no_total_fee'),
        pytest.param(15.31, 5.54, 8.66, 1.11, id='net_positive'),
        pytest.param(10.35, 5.54, 8.66, -3.85, id='net_negative'),
    ),
)
def test_return_usd_sql(
        db_session: Session,
        item_factory: ItemFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        expected_return: float | None,
) -> None:
    item = item_factory.get(sale_total=sale_total, shipping=shipping, sale_fee=sale_fee)
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.return_usd == expected_return


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'usd_to_jpy_rate', 'expected_return'),
    (
        pytest.param(None, None, None, None, None, id='no_fees'),
        pytest.param(9.64, 3.21, None, 140.55, None, id='no_return_usd'),
        pytest.param(9.64, 3.21, 2.87, None, None, id='no_exchange_rate'),
        pytest.param(9.64, 3.21, 2.87, 140.55, 500, id='net_positive'),
        pytest.param(5.49, 3.27, 2.99, 140.55, -108, id='net_negative'),
    ),
)
def test_return_jpy_python(
        item_factory: ItemFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_return: int | None,
) -> None:
    item = item_factory.get(
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.return_jpy == expected_return


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'usd_to_jpy_rate', 'expected_return'),
    (
        pytest.param(None, None, None, None, None, id='no_fees'),
        pytest.param(9.64, 3.21, None, 140.55, None, id='no_return_usd'),
        pytest.param(9.64, 3.21, 2.87, None, None, id='no_exchange_rate'),
        pytest.param(9.64, 3.21, 2.87, 140.55, 500, id='net_positive'),
        pytest.param(5.49, 3.27, 2.99, 140.55, -108, id='net_negative'),
    ),
)
def test_return_jpy_sql(
        db_session: Session,
        item_factory: ItemFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_return: int | None,
) -> None:
    item = item_factory.get(
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.return_jpy == expected_return


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_net',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
    ),
)
def test_net_jpy_python(
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_net: int | None,
) -> None:
    item = item_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_jpy == expected_net


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_net',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
    ),
)
def test_net_jpy_sql(
        db_session: Session,
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_net: int | None,
) -> None:
    item = item_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.net_jpy == expected_net


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_percent',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(0, {}, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
    ),
)
def test_net_percent_python(
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_percent: float | None,
) -> None:
    item = item_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_percent == expected_percent


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_percent',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(0, {}, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
    ),
)
def test_net_percent_sql(
        db_session: Session,
        item_factory: ItemFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_percent: float | None,
) -> None:
    item = item_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    db_session.add(item)
    db_session.commit()

    result = crud.get_item(db=db_session, item_id=item.id)
    assert result is not None
    assert result.net_percent == expected_percent
