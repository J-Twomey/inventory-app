from collections.abc import Callable
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import (
    crud,
    item_enums,
    schemas,
)
from src.models import (
    Item,
    Refund,
)

from .conftest import (
    ItemFactory,
    closed_item,
    form_field_names,
)


def test_read_root(client: TestClient) -> None:
    response = client.get('/')
    assert response.status_code == 200


def test_view_items_no_items(client: TestClient) -> None:
    response = client.get('/items_view')
    assert response.status_code == 200


def test_view_items_shows_seeded_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='SMOKE_TEST_ITEM')
    db_session.add(item)
    db_session.flush()

    response = client.get('/items_view')
    assert response.status_code == 200
    assert 'SMOKE_TEST_ITEM' in response.text


def test_submit_edit_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='BEFORE_EDIT')
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'name': 'AFTER_EDIT'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers['location'] == '/items_view'
    assert item.name == 'AFTER_EDIT'


def test_edit_item_form_field_names_match_schema(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()

    response = client.get(f'/edit/{item.id}')
    assert form_field_names(response.text) <= set(schemas.ItemUpdate.model_fields)


def test_submit_edit_item_purchase_grading_fields(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(purchase_grading_company=item_enums.GradingCompany.RAW)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={
            'purchase_grading_company': 'PSA',
            'purchase_grade': '9',
            'purchase_cert': '12345',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert item.purchase_grading_company == item_enums.GradingCompany.PSA
    assert item.purchase_grade == 9.0
    assert item.purchase_cert == 12345


def test_submit_edit_item_group_discount_on_sold_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = closed_item(item_factory)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'group_discount': 'on'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert item.group_discount is True


def test_submit_edit_item_group_discount_on_unsold_item_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(status=item_enums.Status.STORAGE)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'group_discount': 'on'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'Group discount cannot be assigned to an unsold item' in response.text
    assert item.group_discount is False


def test_submit_edit_item_list_type_on_listed_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.SELL,
        list_type=item_enums.ListingType.FIXED,
        list_price=2000.0,
        list_date=date(2026, 1, 1),
    )
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'list_type': 'AUCTION'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert item.list_type == item_enums.ListingType.AUCTION


def test_submit_add_item_form(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        '/add_item',
        data={
            'name': 'FORM_CREATED',
            'set_name': 'Jungle',
            'category': 'CARD',
            'language': 'KOREAN',
            'qualifiers': ['UNLIMITED', 'CRYSTAL'],
            'details': '',
            'purchase_date': '2025-05-05',
            'purchase_price': '1000',
            'status': 'STORAGE',
            'intent': 'SELL',
            'import_fee': '0',
            'purchase_grading_company': 'RAW',
            'purchase_grade': '',
            'purchase_cert': '',
            'list_price': '',
            'list_type': 'NO_LIST',
            'list_date': '',
            'sale_total': '',
            'sale_date': '',
            'shipping': '',
            'sale_fee': '',
            'usd_to_jpy_rate': '',
            'object_variant': 'STANDARD',
            'audit_target': 'on',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers['location'] == '/items_view'

    item = db_session.query(Item).filter(Item.name == 'FORM_CREATED').one()
    assert item.language == item_enums.Language.KOREAN
    assert item.qualifiers == [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL]
    assert item.audit_target is True
    assert item.group_discount is False


def test_view_items_search_with_pagination_params(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    items = [
        item_factory.get(idx=1, name='FINDME', language=item_enums.Language.KOREAN),
        item_factory.get(idx=2, name='HIDDEN', language=item_enums.Language.GERMAN),
    ]
    db_session.add_all(items)
    db_session.flush()

    response = client.get(
        '/items_view',
        params={
            'language': 'KOREAN',
            'name': '',
            'skip': 0,
            'show_limit': 100,
        },
    )
    assert response.status_code == 200
    assert 'FINDME' in response.text
    assert 'HIDDEN' not in response.text


def test_submit_edit_grading_record(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        is_cracked_flags=[False],
    )
    record = item.submissions[0]

    form_page = client.get(f'/grading_record_edit/{record.id}')
    assert form_page.status_code == 200

    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '25', 'grade': '9.5', 'cert': '222', 'is_cracked': 'on'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.grading_fee == 25
    assert record.grade == 9.5
    assert record.cert == 222
    assert record.is_cracked is True


def test_submit_edit_grading_record_partial_required_fields_shows_error(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory()
    record = item.submissions[0]
    assert record.grading_fee is None
    assert record.grade is None
    assert record.cert is None

    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '', 'grade': '9.5', 'cert': ''},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert (
        'A grading record requires grading fee, grade, and cert to all be set, or all be none'
        in response.text
    )
    assert record.grade is None


def test_submit_edit_grading_record_partial_removal_shows_error(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        intent=item_enums.Intent.GRADE,
    )
    record = item.submissions[0]

    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '10', 'grade': '9.0', 'cert': ''},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert (
        'A grading record requires grading fee, grade, and cert to all be set, or all be none'
        in response.text
    )
    assert record.cert == 111


def test_submit_edit_grading_record_removing_grading_info_sets_item_status_to_submitted(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        intent=item_enums.Intent.GRADE,
        status=item_enums.Status.STORAGE,
    )
    record = item.submissions[0]

    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '', 'grade': '', 'cert': ''},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.grading_fee is None
    assert record.grade is None
    assert record.cert is None
    assert item.status == item_enums.Status.SUBMITTED


def test_add_submission_duplicate_sub_number_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    first_item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    second_item = item_factory.get(idx=2, intent=item_enums.Intent.GRADE)
    db_session.add_all([first_item, second_item])
    db_session.flush()

    first = client.post(
        '/add_submission',
        data={
            'submission_number': '5',
            'submission_company': 'PSA',
            'submission_date': '2025-06-01',
            'item_ids': [str(first_item.id)],
        },
        follow_redirects=False,
    )
    assert first.status_code == 303

    duplicate = client.post(
        '/add_submission',
        data={
            'submission_number': '5',
            'submission_company': 'PSA',
            'submission_date': '2025-06-01',
            'item_ids': [str(second_item.id)],
        },
        follow_redirects=False,
    )
    assert duplicate.status_code == 200
    assert 'Submission number 5 is not valid' in duplicate.text


def test_add_submission_duplicate_item_ids_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        '/add_submission',
        data={
            'submission_number': '5',
            'submission_company': 'PSA',
            'submission_date': '2025-06-01',
            'item_ids': [str(item.id), str(item.id)],
        },
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'Cannot add the same item to a submission more than once' in response.text
    assert crud.get_total_number_of_submissions(db_session) == 0


def test_add_submission_negative_sub_number_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    submission = client.post(
        '/add_submission',
        data={
            'submission_number': '-1',
            'submission_company': 'PSA',
            'submission_date': '2025-06-01',
            'item_ids': [str(item.id)],
        },
        follow_redirects=False,
    )
    assert submission.status_code == 200


def test_submit_edit_grading_record_unchecked_checkbox_clears_is_cracked(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        is_cracked_flags=[True],
        intent=item_enums.Intent.GRADE,
    )
    record = item.submissions[0]

    # Browsers omit unchecked checkboxes from the form body entirely
    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '', 'grade': '', 'cert': ''},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.is_cracked is False


def test_submit_edit_item_closed_to_non_closed_without_removing_sale_info_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = closed_item(item_factory)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'status': 'STORAGE'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'requires the following fields to be null' in response.text
    db_session.refresh(item)
    assert item.status == item_enums.Status.CLOSED


def test_submit_edit_item_closed_to_non_closed_with_removing_sale_info(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = closed_item(item_factory)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={
            'status': 'STORAGE',
            'sale_total': '',
            'sale_date': '',
            'shipping': '',
            'sale_fee': '',
            'usd_to_jpy_rate': '',
            'list_price': '',
            'list_date': '',
            'list_type': 'NO_LIST',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    db_session.refresh(item)
    assert item.status == item_enums.Status.STORAGE
    assert item.sale_total is None
    assert item.sale_date is None
    assert item.list_price is None


def test_submit_edit_item_closed_to_listed_keeps_existing_list_fields(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = closed_item(item_factory)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={
            'status': 'LISTED',
            'sale_total': '',
            'sale_date': '',
            'shipping': '',
            'sale_fee': '',
            'usd_to_jpy_rate': '',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    db_session.refresh(item)
    assert item.status == item_enums.Status.LISTED
    assert item.list_price == 2000.0
    assert item.sale_total is None


def test_submit_edit_item_invalid_intent_status_pair_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = closed_item(item_factory)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'status': 'SUBMITTED'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'Cannot update item with intent of SELL to have status of SUBMITTED' in response.text
    db_session.refresh(item)
    assert item.status == item_enums.Status.CLOSED


def test_submit_edit_item_removing_required_field_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, name='KEEP_ME')
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'name': '', 'details': 'edited'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'The following fields cannot be removed:' in response.text
    assert 'name' in response.text
    db_session.refresh(item)
    assert item.name == 'KEEP_ME'
    assert item.details is None


def test_submit_edit_item_to_submitted_shows_error(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'status': 'SUBMITTED'},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert 'An item can only be set to SUBMITTED by adding it to a submission' in response.text
    db_session.refresh(item)
    assert item.status == item_enums.Status.STORAGE


def test_show_add_refund_form(client: TestClient) -> None:
    response = client.get('/add_refund')
    assert response.status_code == 200
    assert 'Add New Refund' in response.text


def test_submit_add_refund_form(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        '/add_refund',
        data={
            'item_id': '',
            'refund_amount_usd': '12.50',
            'refund_date': '2025-06-01',
            'refund_reason': 'DAMAGE',
            'usd_to_jpy_rate': '150',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers['location'] == '/'

    refund = db_session.query(Refund).one()
    assert refund.item_id is None
    assert refund.refund_amount_usd == 12.50
    assert refund.refund_reason == item_enums.RefundReason.DAMAGE
    assert refund.refund_amount_jpy == 1875


def test_submit_add_refund_form_linked_to_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()

    response = client.post(
        '/add_refund',
        data={
            'item_id': str(item.id),
            'refund_amount_usd': '20',
            'refund_date': '2025-06-01',
            'refund_reason': 'LOSS',
            'usd_to_jpy_rate': '150',
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    refund = db_session.query(Refund).one()
    assert refund.item_id == item.id
    assert refund.item is not None
    assert refund.item.id == item.id


def test_submit_add_refund_form_missing_required_field(client: TestClient) -> None:
    response = client.post(
        '/add_refund',
        data={
            'refund_amount_usd': '',
            'refund_date': '2025-06-01',
            'refund_reason': 'OTHER',
            'usd_to_jpy_rate': '150',
        },
        follow_redirects=False,
    )
    assert response.status_code == 422


def test_view_refunds_no_refunds(client: TestClient) -> None:
    response = client.get('/refunds_view')
    assert response.status_code == 200
    assert 'No refunds found.' in response.text


def test_view_refunds_shows_refund(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='REFUNDED_ITEM')
    db_session.add(item)
    db_session.flush()
    db_session.add(
        Refund(
            item_id=item.id,
            refund_amount_usd=12.50,
            refund_date=date(2025, 6, 1),
            refund_reason=item_enums.RefundReason.DAMAGE,
            usd_to_jpy_rate=150.0,
        ),
    )
    db_session.flush()

    response = client.get('/refunds_view')
    assert response.status_code == 200
    assert 'REFUNDED_ITEM' in response.text
    assert '$12.50' in response.text
    assert 'DAMAGE' in response.text
    assert 'No refunds found.' not in response.text
