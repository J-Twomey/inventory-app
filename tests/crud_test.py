from datetime import date

from sqlalchemy.orm import Session

import src.crud as crud
import src.item_enums as item_enums
import src.schemas as schemas


def test_create_item(db_session: Session) -> None:
    item = schemas.ItemCreate(
        name='TESTER',
        set_name='Base Set',
        category=item_enums.Category.CARD,
        language=item_enums.Language.KOREAN,
        qualifiers=[item_enums.Qualifier.UNLIMITED],
        details='Mint',
        purchase_date=date(2025, 5, 5),
        purchase_price=1000,
        status=item_enums.Status.CLOSED,
        intent=item_enums.Intent.SELL,
        grading_fee={1: 600, 2: 399},
        grade=10.,
        grading_company=item_enums.GradingCompany.PSA,
        cert=123456789,
        submission_number=[1, 2],
        list_price=500.,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 10, 10),
        sale_total=550.,
        sale_date=date(2025, 10, 11),
        shipping=25.,
        sale_fee=25.,
        usd_to_jpy_rate=150.0,
        group_discount=False,
        object_variant=item_enums.ObjectVariant.STANDARD,
        audit_target=False,
    )
    db_item = crud.create_item(db_session, item)
    assert db_item.id is not None
    assert db_item.name == 'TESTER'
    assert db_item.grading_fee_total == 999
