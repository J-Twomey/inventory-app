import pytest
from sqlalchemy.orm import Session

import src.crud as crud
from .conftest import ItemFactory


# @pytest.mark.parametrize(
#     ('purchase_price', 'grading_fees', 'import_fee', 'expected_total'),
#     (
#         pytest.param(10, {}, 0, 10, id='no_grading_fees'),
#         pytest.param(10, {1: 100}, 0, 110, id='single_grading_fee'),
#         pytest.param(10, {1: 100, 2: 200}, 0, 310, id='multiple_grading_fees'),
#         pytest.param(10, {}, 11, 21, id='with_import_fee'),
#     ),
# )
# def test_total_cost_python(
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         import_fee: int,
#         expected_total: int,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         import_fee=import_fee,
#         grading_fee=grading_fees,
#     )
#     assert item.total_cost == expected_total


# @pytest.mark.parametrize(
#     ('purchase_price', 'grading_fees', 'import_fee', 'expected_total'),
#     (
#         pytest.param(10, {}, 0, 10, id='no_grading_fees'),
#         pytest.param(10, {1: 100}, 0, 110, id='single_grading_fee'),
#         pytest.param(10, {1: 100, 2: 200}, 0, 310, id='multiple_grading_fees'),
#         pytest.param(10, {}, 11, 21, id='with_import_fee'),
#     ),
# )
# def test_total_cost_sql(
#         db_session: Session,
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         import_fee: int,
#         expected_total: int,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         import_fee=import_fee,
#         grading_fee=grading_fees,
#     )
#     db_session.add(item)
#     db_session.commit()

#     result = crud.get_item(db=db_session, item_id=item.id)
#     assert result is not None
#     assert result.total_cost == expected_total


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


# @pytest.mark.parametrize(
#     (
#         'purchase_price',
#         'grading_fees',
#         'sale_total',
#         'shipping',
#         'sale_fee',
#         'usd_to_jpy_rate',
#         'expected_net',
#     ),
#     (
#         pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
#         pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
#         pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
#         pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
#     ),
# )
# def test_net_jpy_python(
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         sale_total: float | None,
#         shipping: float | None,
#         sale_fee: float | None,
#         usd_to_jpy_rate: float | None,
#         expected_net: int | None,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         grading_fee=grading_fees,
#         sale_total=sale_total,
#         shipping=shipping,
#         sale_fee=sale_fee,
#         usd_to_jpy_rate=usd_to_jpy_rate,
#     )
#     assert item.net_jpy == expected_net


# @pytest.mark.parametrize(
#     (
#         'purchase_price',
#         'grading_fees',
#         'sale_total',
#         'shipping',
#         'sale_fee',
#         'usd_to_jpy_rate',
#         'expected_net',
#     ),
#     (
#         pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
#         pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
#         pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
#         pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
#     ),
# )
# def test_net_jpy_sql(
#         db_session: Session,
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         sale_total: float | None,
#         shipping: float | None,
#         sale_fee: float | None,
#         usd_to_jpy_rate: float | None,
#         expected_net: int | None,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         grading_fee=grading_fees,
#         sale_total=sale_total,
#         shipping=shipping,
#         sale_fee=sale_fee,
#         usd_to_jpy_rate=usd_to_jpy_rate,
#     )
#     db_session.add(item)
#     db_session.commit()

#     result = crud.get_item(db=db_session, item_id=item.id)
#     assert result is not None
#     assert result.net_jpy == expected_net


# @pytest.mark.parametrize(
#     (
#         'purchase_price',
#         'grading_fees',
#         'sale_total',
#         'shipping',
#         'sale_fee',
#         'usd_to_jpy_rate',
#         'expected_percent',
#     ),
#     (
#         pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
#         pytest.param(0, {}, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
#         pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
#         pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
#         pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
#     ),
# )
# def test_net_percent_python(
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         sale_total: float | None,
#         shipping: float | None,
#         sale_fee: float | None,
#         usd_to_jpy_rate: float | None,
#         expected_percent: float | None,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         grading_fee=grading_fees,
#         sale_total=sale_total,
#         shipping=shipping,
#         sale_fee=sale_fee,
#         usd_to_jpy_rate=usd_to_jpy_rate,
#     )
#     assert item.net_percent == expected_percent


# @pytest.mark.parametrize(
#     (
#         'purchase_price',
#         'grading_fees',
#         'sale_total',
#         'shipping',
#         'sale_fee',
#         'usd_to_jpy_rate',
#         'expected_percent',
#     ),
#     (
#         pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
#         pytest.param(0, {}, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
#         pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
#         pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
#         pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
#     ),
# )
# def test_net_percent_sql(
#         db_session: Session,
#         item_factory: ItemFactory,
#         purchase_price: int,
#         grading_fees: dict[int, int],
#         sale_total: float | None,
#         shipping: float | None,
#         sale_fee: float | None,
#         usd_to_jpy_rate: float | None,
#         expected_percent: float | None,
# ) -> None:
#     item = item_factory.get(
#         purchase_price=purchase_price,
#         grading_fee=grading_fees,
#         sale_total=sale_total,
#         shipping=shipping,
#         sale_fee=sale_fee,
#         usd_to_jpy_rate=usd_to_jpy_rate,
#     )
#     db_session.add(item)
#     db_session.commit()

#     result = crud.get_item(db=db_session, item_id=item.id)
#     assert result is not None
#     assert result.net_percent == expected_percent


# def test_to_display(item_factory: ItemFactory) -> None:
#     display_item = item_factory.get(
#         purchase_price=800,
#         qualifiers=[item_enums.Qualifier.CRYSTAL],
#         status=item_enums.Status.CLOSED.value,
#         import_fee=200,
#         # grading_fee={1: 100, 2: 200},
#         grading_company=item_enums.GradingCompany.BGS.value,
#         purchase_grade=10.,
#         purchase_cert=999999999,
#         list_price=100.,
#         list_type=item_enums.ListingType.FIXED.value,
#         list_date=date(2025, 5, 6),
#         sale_total=200.,
#         sale_date=date(2025, 5, 7),
#         shipping=10.,
#         sale_fee=20.55,
#         usd_to_jpy_rate=150.99,
#         group_discount=True,
#     ).to_display()

#     # Check that enums are converted properly
#     assert display_item.category == item_enums.Category.CARD
#     assert display_item.language == item_enums.Language.KOREAN
#     assert display_item.qualifiers == [item_enums.Qualifier.CRYSTAL]
#     assert display_item.status == item_enums.Status.CLOSED
#     assert display_item.intent == item_enums.Intent.SELL
#     assert display_item.grading_company == item_enums.GradingCompany.BGS
#     assert display_item.list_type == item_enums.ListingType.FIXED
#     assert display_item.object_variant == item_enums.ObjectVariant.STANDARD

#     # Check that hybrid properties are correctly calculated
#     assert display_item.total_cost == 1300
#     assert display_item.total_fees == 30.55
#     assert display_item.return_usd == 169.45
#     assert display_item.return_jpy == 25585
#     assert display_item.net_jpy == 24285
#     assert display_item.net_percent == 1868.08
