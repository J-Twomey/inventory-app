from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import eq

import src.crud as crud
import src.item_enums as item_enums
import src.models as models
import src.schemas as schemas
from .conftest import (
    GradingRecordFactory,
    ItemCreateFactory,
    ItemFactory,
    SubmissionFactory,
)


def test_create_item_all_nullables_none(
        db_session: Session,
        item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get()
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
    assert db_item.name == 'TESTER'


def test_create_item_all_nullables_provided(
        db_session: Session,
        item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get(
        qualifiers=[item_enums.Qualifier.UNLIMITED],
        status=item_enums.Status.CLOSED,
        details='Mint',
        purchase_grading_company=item_enums.GradingCompany.PSA,
        purchase_grade=10.,
        purchase_cert=123456789,
        list_price=500.,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 10, 10),
        sale_total=550.,
        sale_date=date(2025, 10, 11),
        shipping=25.,
        sale_fee=25.,
        usd_to_jpy_rate=150.0,
    )
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
    assert db_item.name == 'TESTER'
    assert db_item.sale_total == 550.


def test_create_item_multiple_qualifiers(
        db_session: Session,
        item_create_factory: ItemCreateFactory,
) -> None:
    input_qualifiers = [item_enums.Qualifier.REVERSE_HOLO, item_enums.Qualifier.CRYSTAL]
    item = item_create_factory.get(
        qualifiers=input_qualifiers,
    )
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
    assert db_item.qualifiers == input_qualifiers


def test_get_item_returns_correct_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='GET_ITEM_TEST_ITEM')
    db_session.add(item)

    result = crud.get_item(db_session, item.id)
    assert result is not None
    assert result.id == item.id
    assert result.name == 'GET_ITEM_TEST_ITEM'


def test_get_item_no_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='GET_ITEM_TEST_NO_ITEM')
    db_session.add(item)
    db_session.flush()
    result = crud.get_item(db_session, item.id + 1)
    assert result is None


def test_get_newest_items_return_all_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_newest_items(db_session, skip=0, limit=100)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names)
    assert result_ids == ids
    assert result_names == item_names


def test_get_newest_items_skip_newest_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_newest_items(db_session, skip=1, limit=100)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names) - 1
    assert result_ids == ids[:-1]
    assert result_names == item_names[:-1]


def test_get_newest_items_take_multiple_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_newest_items(db_session, skip=0, limit=2)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names) - 1
    assert result_ids == ids[1:]
    assert result_names == item_names[1:]


def test_get_newest_items_skip_all_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_newest_items(db_session, skip=len(item_names), limit=len(item_names) + 1)
    assert len(result) == 0


def test_get_newest_items_no_items(db_session: Session) -> None:
    result = crud.get_newest_items(db_session, skip=0, limit=100)
    assert len(result) == 0


def test_get_total_number_of_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_total_number_of_items(db_session)
    assert result == len(items)


def test_delete_item_by_id_success(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.delete_item_by_id(db_session, ids[-1])
    assert result is True
    assert crud.get_item(db_session, ids[-1]) is None
    assert crud.get_item(db_session, ids[0]) is not None


def test_delete_item_by_id_failure(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.delete_item_by_id(db_session, ids[-1] + 1)
    assert result is False
    for id in ids:
        assert crud.get_item(db_session, id) is not None


def test_search_for_items_no_filters(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearchForm().to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == len(item_names)


def test_search_for_items_simple_case(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, id=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearchForm(name='two').to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].name == 'two'


def test_search_for_items_multiple_search_criteria(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_grading_companies = [
        item_enums.GradingCompany.RAW,
        item_enums.GradingCompany.PSA,
        item_enums.GradingCompany.PSA,
    ]
    item_languages = [
        item_enums.Language.KOREAN,
        item_enums.Language.KOREAN,
        item_enums.Language.GERMAN,
    ]
    grades = [None, 9., 9.]
    certs = [None, 1, 1]
    items = [
        item_factory.get(
            id=i,
            purchase_grading_company=gc,
            language=lang,
            purchase_grade=g,
            purchase_cert=c,
        ) for i, (gc, lang, g, c) in enumerate(
            zip(
                item_grading_companies,
                item_languages,
                grades,
                certs,
            )
        )
    ]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearchForm(
        language='KOREAN',
        grading_company='PSA',
    ).to_item_search()

    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].language == item_enums.Language.KOREAN
    assert result[0].grading_company == item_enums.GradingCompany.PSA


def test_search_for_items_multiple_qualifiers(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_qualifiers = [
        [item_enums.Qualifier.NON_HOLO],
        [item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL],
        [item_enums.Qualifier.CRYSTAL],
        [],
    ]
    items = [item_factory.get(id=i, qualifiers=q) for i, q in enumerate(item_qualifiers)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearchForm(qualifiers=['NON_HOLO', 'CRYSTAL']).to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].qualifiers == [item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL]


def test_edit_item_no_item_found(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(id=1)
    db_session.add(item)
    db_session.flush()
    result = crud.edit_item(db_session, item_id=100, item_update=schemas.ItemUpdate())
    assert result == 404


def test_edit_item_no_changes(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    original_item = item_factory.get()
    db_session.add(original_item)
    db_session.flush()

    result = crud.edit_item(db_session, item_id=original_item.id, item_update=schemas.ItemUpdate())
    assert result == 303

    changed_item = crud.get_item(db_session, original_item.id)
    assert changed_item == original_item


def test_edit_item_single_field(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()
    item_changes = schemas.ItemUpdate(name='new_name')

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.name == 'new_name'


def test_edit_item_enum_field(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()
    item_changes = schemas.ItemUpdate(language=item_enums.Language.INDONESIAN)

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.language == item_enums.Language.INDONESIAN


def test_edit_item_multiple_changes(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()
    item_changes = schemas.ItemUpdate(
        purchase_grade=10.,
        purchase_grading_company=item_enums.GradingCompany.BGS,
    )

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.grading_company == item_enums.GradingCompany.BGS
    assert changed_item.grade == 10.


def test_edit_item_add_new_qualifier(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_session.add(item)
    db_session.flush()
    item_changes = schemas.ItemUpdate(qualifiers=[item_enums.Qualifier.CRYSTAL])

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.qualifiers == [item_enums.Qualifier.CRYSTAL]


def test_edit_item_add_extra_qualifier_to_existing(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(qualifiers=[item_enums.Qualifier.CRYSTAL])
    db_session.add(item)
    db_session.flush()
    # Qualifiers are handled such that the newly added ones should be appended to the existing ones
    new_qualifiers = item.qualifiers + [item_enums.Qualifier.UNLIMITED]
    item_changes = schemas.ItemUpdate(qualifiers=new_qualifiers)

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.qualifiers == [
        item_enums.Qualifier.CRYSTAL,
        item_enums.Qualifier.UNLIMITED,
    ]


def test_build_search_filters_no_special_case() -> None:
    params = {'name': 'Unown', 'set_name': 'Base Set'}
    filters, post_filters = crud.build_search_filters(params)

    assert filters[0].left.key == 'name'
    assert filters[0].right.value == 'Unown'
    assert filters[0].operator is eq
    assert filters[1].left.key == 'set_name'
    assert filters[1].right.value == 'Base Set'
    assert filters[1].operator is eq
    assert post_filters == []


def test_build_search_features_with_post_filter() -> None:
    params = {'name': 'Unown', 'cracked_from': 1}
    expected_post_filters = [('cracked_from', 1)]
    filters, post_filters = crud.build_search_filters(params)

    assert filters[0].left.key == 'name'
    assert filters[0].right.value == 'Unown'
    assert filters[0].operator is eq
    assert post_filters == expected_post_filters


def test_get_total_number_of_submissions_no_subs(db_session: Session) -> None:
    result = crud.get_total_number_of_submissions(db_session)
    assert result == 0


def test_get_total_number_of_submissions(
        db_session: Session,
        submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get()
    db_session.add(submission)
    db_session.flush()

    result = crud.get_total_number_of_submissions(db_session)
    assert result == 1


def get_total_number_of_grading_records_no_records(db_session: Session) -> None:
    result = crud.get_total_number_of_grading_records(db_session)
    assert result == 0


def test_get_total_number_of_grading_records(
        db_session: Session,
        item_factory: ItemFactory,
        submission_factory: SubmissionFactory,
        grading_record_factory: GradingRecordFactory,
) -> None:
    item = item_factory.get()
    submission = submission_factory.get()

    db_session.add_all([item, submission])
    db_session.flush()

    grading_record = grading_record_factory.get(
        item_id=item.id,
        submission_number=submission.submission_number,
    )
    db_session.add(grading_record)
    db_session.flush()

    result = crud.get_total_number_of_grading_records(db_session)
    assert result == 1


def test_get_max_sub_number_no_subs(db_session: Session) -> None:
    result = crud.get_max_sub_number(db_session)
    assert result == 0


def test_get_max_sub_number(
        db_session: Session,
        submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get()
    db_session.add(submission)
    db_session.flush()

    result = crud.get_max_sub_number(db_session)
    assert result == 1


def test_get_max_sub_number_with_skipped_number(
        db_session: Session,
        submission_factory: SubmissionFactory,
) -> None:
    sub_nums = [1, 3]
    submissions = [submission_factory.get(submission_number=s) for s in sub_nums]
    db_session.add_all(submissions)
    db_session.flush()

    result = crud.get_max_sub_number(db_session)
    assert result == max(sub_nums)
