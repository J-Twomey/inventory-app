from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import item_enums
from src.models import Item

from .conftest import ItemFactory


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
        data={'grading_fee': '25', 'grade': '9.5', 'cert': '', 'is_cracked': 'on'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.grading_fee == 25
    assert record.grade == 9.5
    # An empty form field means untouched, not cleared
    assert record.cert == 111
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
        'Adding grading info to a record requires all of grading fee, grade, and cert'
        in response.text
    )
    assert record.grade is None


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
