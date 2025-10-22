import pytest
from datetime import date
from typing import Callable

from sqlalchemy.orm import Session

import src.crud as crud
import src.item_enums as item_enums
from src.models import Item
from .conftest import ItemFactory


def test_total_grading_fees(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1, 2, 3],
        submission_numbers=[1, 2, 3],
        grading_fees=[10, 20, 30],
        grades=[1, 1, 1],
        certs=[1, 2, 3],
        is_cracked_flags=[True, True, False],
    )
    expected_total = 60
    # Python side
    assert item_with_submissions.total_grading_fees == expected_total
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.total_grading_fees == expected_total


def test_total_cost(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1, 2],
        submission_numbers=[1, 2],
        grading_fees=[10, 20],
        grades=[1, 1],
        certs=[1, 2],
        is_cracked_flags=[True, False],
        purchase_price=1000,
        import_fee=100,
    )
    expected_total = 1130
    # Python side
    assert item_with_submissions.total_cost == expected_total
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.total_cost == expected_total


def test_grading_company_no_submission_no_crack(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=3,
        purchase_grade=1,
        purchase_cert=1,
        cracked_from_purchase=False,
    )
    expected_grading_company = 3
    # Python side
    assert item.grading_company == expected_grading_company
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.grading_company == expected_grading_company


def test_grading_company_no_submission_cracked_from_purchase(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=3,
        purchase_grade=1,
        purchase_cert=1,
        cracked_from_purchase=True,
    )
    expected_grading_company = 0
    # Python side
    assert item.grading_company == expected_grading_company
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.grading_company == expected_grading_company


def test_grading_company_latest_sub_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[1],
        certs=[1],
        is_cracked_flags=[True],
        submission_companies=[3],
    )
    expected_grading_company = 0
    # Python side
    assert item_with_submissions.grading_company == expected_grading_company
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.grading_company == expected_grading_company


def test_grading_company_latest_sub_not_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[1],
        certs=[1],
        is_cracked_flags=[False],
        submission_companies=[3],
    )
    expected_grading_company = 3
    # Python side
    assert item_with_submissions.grading_company == expected_grading_company
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.grading_company == expected_grading_company


def test_grade_no_submission_no_crack(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=1,
        purchase_grade=5,
        purchase_cert=1,
        cracked_from_purchase=False,
    )
    expected_grade = 5
    # Python side
    assert item.grade == expected_grade
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.grade == expected_grade


def test_grade_no_submission_cracked_from_purchase(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=1,
        purchase_grade=5,
        purchase_cert=1,
        cracked_from_purchase=True,
    )
    expected_grade = None
    # Python side
    assert item.grade == expected_grade
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.grade == expected_grade


def test_grade_latest_sub_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[5],
        certs=[1],
        is_cracked_flags=[True],
        submission_companies=[3],
    )
    expected_grade = None
    # Python side
    assert item_with_submissions.grade == expected_grade
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.grade == expected_grade


def test_grade_latest_sub_not_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[5],
        certs=[1],
        is_cracked_flags=[False],
        submission_companies=[3],
    )
    expected_grade = 5
    # Python side
    assert item_with_submissions.grade == expected_grade
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.grade == expected_grade


def test_cert_no_submission_no_crack(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=1,
        purchase_grade=1,
        purchase_cert=123,
        cracked_from_purchase=False,
    )
    expected_cert = 123
    # Python side
    assert item.cert == expected_cert
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.cert == expected_cert


def test_cert_no_submission_cracked_from_purchase(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        purchase_grading_company=1,
        purchase_grade=1,
        purchase_cert=123,
        cracked_from_purchase=True,
    )
    expected_cert = None
    # Python side
    assert item.cert == expected_cert
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.cert == expected_cert


def test_cert_latest_sub_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[1],
        certs=[123],
        is_cracked_flags=[True],
        submission_companies=[3],
    )
    expected_cert = None
    # Python side
    assert item_with_submissions.cert == expected_cert
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.cert == expected_cert


def test_cert_latest_sub_not_cracked(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
) -> None:
    item_with_submissions = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[10],
        grades=[1],
        certs=[123],
        is_cracked_flags=[False],
        submission_companies=[3],
    )
    expected_cert = 123
    # Python side
    assert item_with_submissions.cert == expected_cert
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item_with_submissions.id)
    assert db_item is not None
    assert db_item.cert == expected_cert


@pytest.mark.parametrize(
    ('shipping', 'sale_fee', 'expected_total'),
    (
        pytest.param(None, None, None, id='no_fees'),
        pytest.param(None, 8.7, None, id='no_shipping'),
        pytest.param(5.5, None, None, id='no_sale_fee'),
        pytest.param(5.5, 8.7, 14.2, id='with_fees'),
    ),
)
def test_total_fees(
        db_session: Session,
        item_factory: ItemFactory,
        shipping: float | None,
        sale_fee: float | None,
        expected_total: float | None,
) -> None:
    item = item_factory.get(shipping=shipping, sale_fee=sale_fee)
    # Python side
    assert item.total_fees == expected_total
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.total_fees == expected_total


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
def test_return_usd(
        db_session: Session,
        item_factory: ItemFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        expected_return: float | None,
) -> None:
    item = item_factory.get(sale_total=sale_total, shipping=shipping, sale_fee=sale_fee)
    # Python side
    assert item.return_usd == expected_return
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.return_usd == expected_return


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
def test_return_jpy(
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
    # Python side
    assert item.return_jpy == expected_return
    # DB side
    db_session.add(item)
    db_session.commit()
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.return_jpy == expected_return


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fee',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_net',
    ),
    (
        pytest.param(10, 100, None, None, None, None, None, id='no_sale'),
        pytest.param(10, 100, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
        pytest.param(1000, 100, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
        pytest.param(10, 1000, 5.49, 3.27, 2.99, 140.55, -1118, id='negative_ret_net_neg'),
    ),
)
def test_net_jpy(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
        purchase_price: int,
        grading_fee: int,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_net: int | None,
) -> None:
    item = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[grading_fee],
        grades=[1],
        certs=[1],
        is_cracked_flags=[False],
        purchase_price=purchase_price,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    # Python side
    assert item.net_jpy == expected_net
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.net_jpy == expected_net


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fee',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_percent',
    ),
    (
        pytest.param(10, 100, None, None, None, None, None, id='no_sale'),
        pytest.param(0, None, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
        pytest.param(10, 100, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
        pytest.param(1000, 100, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
        pytest.param(10, 100, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
    ),
)
def test_net_percent(
        db_session: Session,
        item_with_submissions_factory: Callable[..., Item],
        purchase_price: int,
        grading_fee: int | None,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_percent: float | None,
) -> None:
    item = item_with_submissions_factory(
        grading_record_ids=[1],
        submission_numbers=[1],
        grading_fees=[grading_fee],
        grades=[1],
        certs=[1],
        is_cracked_flags=[False],
        purchase_price=purchase_price,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    # Python side
    assert item.net_percent == expected_percent
    # DB side
    db_item = crud.get_item(db=db_session, item_id=item.id)
    assert db_item is not None
    assert db_item.net_percent == expected_percent


def test_to_display(item_factory: ItemFactory) -> None:
    display_item = item_factory.get(
        purchase_price=800,
        qualifiers=[item_enums.Qualifier.CRYSTAL],
        status=item_enums.Status.CLOSED.value,
        import_fee=200,
        purchase_grading_company=item_enums.GradingCompany.BGS.value,
        purchase_grade=10.,
        purchase_cert=999999999,
        list_price=100.,
        list_type=item_enums.ListingType.FIXED.value,
        list_date=date(2025, 5, 6),
        sale_total=200.,
        sale_date=date(2025, 5, 7),
        shipping=10.,
        sale_fee=20.55,
        usd_to_jpy_rate=150.99,
        group_discount=True,
    ).to_display()

    # Check that enums are converted properly
    assert display_item.category == 'Card'
    assert display_item.language == 'Korean'
    assert display_item.qualifiers == ['Crystal']
    assert display_item.status == 'Closed'
    assert display_item.intent == 'Sell'
    assert display_item.grading_company == 'BGS'
    assert display_item.list_type == 'Fixed'
    assert display_item.object_variant == 'Standard'

    # Check that hybrid properties are correctly calculated
    assert display_item.total_cost == 1000
    assert display_item.total_fees == 30.55
    assert display_item.return_usd == 169.45
    assert display_item.return_jpy == 25585
    assert display_item.net_jpy == 24585
    assert display_item.net_percent == 2458.5
