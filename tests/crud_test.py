from datetime import date

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import eq

from src import (
    crud,
    item_enums,
    models,
    schemas,
)

from .conftest import (
    GradingRecordFactory,
    ItemCreateFactory,
    ItemFactory,
    RefundCreateFactory,
    RefundFactory,
    SubmissionFactory,
)


def test_create_item_all_nullables_none(
    db_session: Session,
    item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get()
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None
    assert db_item == item_from_db
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
        purchase_grade=10.0,
        purchase_cert=123456789,
        list_price=500.0,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 10, 10),
        sale_total=550.0,
        sale_date=date(2025, 10, 11),
        shipping=25.0,
        sale_fee=25.0,
        usd_to_jpy_rate=150.0,
    )
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None
    assert db_item == item_from_db
    assert db_item.name == 'TESTER'
    assert db_item.sale_total == 550.0


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
    assert db_item.id is not None
    assert db_item == item_from_db
    assert db_item.qualifiers == input_qualifiers


def test_create_item_with_submitted_status_rejected(
    db_session: Session,
    item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get(
        status=item_enums.Status.SUBMITTED,
        intent=item_enums.Intent.GRADE,
    )
    with pytest.raises(
        ValueError,
        match='A new item cannot be created with a status of SUBMITTED',
    ):
        crud.create_item(db_session, item)

    assert db_session.query(models.Item).count() == 0


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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    result = crud.get_total_number_of_items(db_session)
    assert result == len(items)


def test_delete_item_by_id_success(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
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
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
    ids = [i.id for i in items]
    db_session.add_all(items)
    db_session.flush()

    result = crud.delete_item_by_id(db_session, ids[-1] + 1)
    assert result is False
    for i in ids:
        assert crud.get_item(db_session, i) is not None


def test_search_for_items_no_filters(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item_names = ['one']
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearch()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == len(item_names)


def test_search_for_items_simple_case(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n, idx=i) for i, n in enumerate(item_names)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearch(name='two')
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
    grades = [None, 9.0, 9.0]
    certs = [None, 1, 1]
    items = [
        item_factory.get(
            idx=i,
            purchase_grading_company=gc,
            language=lang,
            purchase_grade=g,
            purchase_cert=c,
        )
        for i, (gc, lang, g, c) in enumerate(
            zip(
                item_grading_companies,
                item_languages,
                grades,
                certs,
                strict=True,
            ),
        )
    ]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearch(
        language=item_enums.Language.KOREAN,
        grading_company=item_enums.GradingCompany.PSA,
    )

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
    items = [item_factory.get(idx=i, qualifiers=q) for i, q in enumerate(item_qualifiers)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearch(
        qualifiers=[item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL],
    )
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].qualifiers == [item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL]


def test_search_for_items_cracked_from_purchase(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    cracked_flags = [False, False, True]
    items = [item_factory.get(idx=i, cracked_from_purchase=f) for i, f in enumerate(cracked_flags)]
    db_session.add_all(items)
    db_session.flush()

    search_params = schemas.ItemSearch(cracked_from_purchase=True)
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].cracked_from_purchase is True

    search_params = schemas.ItemSearch(cracked_from_purchase=False)
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 2
    assert all(item.cracked_from_purchase is False for item in result)


def test_edit_item_no_item_found(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1)
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
        purchase_grade=10.0,
        purchase_grading_company=item_enums.GradingCompany.BGS,
    )

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.grading_company == item_enums.GradingCompany.BGS
    assert changed_item.grade == 10.0


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
    new_qualifiers = [*item.qualifiers, item_enums.Qualifier.UNLIMITED]
    item_changes = schemas.ItemUpdate(qualifiers=new_qualifiers)

    result = crud.edit_item(db_session, item_id=item.id, item_update=item_changes)
    assert result == 303

    changed_item = crud.get_item(db_session, item.id)
    assert changed_item is not None
    assert changed_item.qualifiers == [
        item_enums.Qualifier.CRYSTAL,
        item_enums.Qualifier.UNLIMITED,
    ]


def test_edit_item_rejects_invalid_merged_state(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.SELL,
        list_price=10.0,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 6, 1),
    )
    db_session.add(item)
    db_session.flush()
    item_changes = schemas.ItemUpdate(
        status=item_enums.Status.STORAGE,
        list_type=item_enums.ListingType.NO_LIST,
    )

    with pytest.raises(ValueError, match='requires the following fields to be null'):
        crud.edit_item(db_session, item_id=item.id, item_update=item_changes)

    unchanged_item = crud.get_item(db_session, item.id)
    assert unchanged_item is not None
    assert unchanged_item.status == item_enums.Status.LISTED
    assert unchanged_item.list_price == 10.0


def test_edit_item_to_submitted_without_active_record_rejected(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    update = schemas.ItemUpdate(status=item_enums.Status.SUBMITTED)
    with pytest.raises(
        ValueError,
        match='An item can only be set to SUBMITTED by adding it to a submission',
    ):
        crud.edit_item(db_session, item.id, update)

    db_session.refresh(item)
    assert item.status == item_enums.Status.STORAGE


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
    params = {'name': 'Unown', 'grading_company': item_enums.GradingCompany.PSA}
    expected_post_filters = [('grading_company', item_enums.GradingCompany.PSA)]
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
        submission_id=submission.id,
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
    sub_ids = [0, 1]
    sub_nums = [1, 3]
    submissions = [
        submission_factory.get(idx=i, submission_number=s)
        for i, s in zip(sub_ids, sub_nums, strict=True)
    ]
    db_session.add_all(submissions)
    db_session.flush()

    result = crud.get_max_sub_number(db_session)
    assert result == max(sub_nums)


def test_create_submission_duplicate_item_ids_rejected(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    submission_summary = schemas.SubmissionCreate(
        submission_number=1,
        submission_company=item_enums.GradingCompany.PSA,
    )

    with pytest.raises(
        ValueError,
        match='Cannot add the same item to a submission more than once',
    ):
        crud.create_submission(db_session, submission_summary, [item.id, item.id])

    assert crud.get_max_sub_number(db_session) == 0
    db_session.refresh(item)
    assert item.status == item_enums.Status.STORAGE


def test_create_submission_sets_item_to_submitted(
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(idx=1, intent=item_enums.Intent.GRADE)
    db_session.add(item)
    db_session.flush()

    submission_summary = schemas.SubmissionCreate(
        submission_number=1,
        submission_company=item_enums.GradingCompany.PSA,
        submission_date=date(2026, 1, 1),
    )
    crud.create_submission(db_session, submission_summary, [item.id])

    db_session.refresh(item)
    assert item.status == item_enums.Status.SUBMITTED
    assert len(item.submissions) == 1
    assert item.submissions[0].grade is None
    assert item.submissions[0].is_cracked is False


def test_edit_submission_return_date_before_submission_date_rejected(
    db_session: Session,
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get(submission_date=date(2026, 1, 10))
    db_session.add(submission)
    db_session.flush()

    with pytest.raises(ValueError, match='Return date cannot be before submission date'):
        crud.edit_submission_single_field(
            db_session,
            submission.id,
            'return_date',
            date(2026, 1, 5),
        )

    db_session.refresh(submission)
    assert submission.return_date is None


def test_edit_submission_submission_date_after_return_date_rejected(
    db_session: Session,
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get(return_date=date(2026, 1, 10))
    db_session.add(submission)
    db_session.flush()

    with pytest.raises(ValueError, match='Return date cannot be before submission date'):
        crud.edit_submission_single_field(
            db_session,
            submission.id,
            'submission_date',
            date(2026, 1, 20),
        )

    db_session.refresh(submission)
    assert submission.submission_date is None


def test_edit_submission_return_date_on_or_after_submission_date_allowed(
    db_session: Session,
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get(submission_date=date(2026, 1, 10))
    db_session.add(submission)
    db_session.flush()

    crud.edit_submission_single_field(
        db_session,
        submission.id,
        'return_date',
        date(2026, 1, 10),
    )

    db_session.refresh(submission)
    assert submission.return_date == date(2026, 1, 10)


def test_delete_grading_record_returns_unsold_item_to_storage(
    db_session: Session,
    item_factory: ItemFactory,
    submission_factory: SubmissionFactory,
    grading_record_factory: GradingRecordFactory,
) -> None:
    item = item_factory.get(idx=1, status=item_enums.Status.SUBMITTED)
    submission = submission_factory.get(idx=1)
    db_session.add_all([item, submission])
    db_session.flush()
    record = grading_record_factory.get(idx=1, item_id=item.id, submission_id=submission.id)
    db_session.add(record)
    db_session.flush()

    assert crud.delete_grading_record_by_id(db_session, record.id) is True

    db_session.refresh(item)
    assert item.status == item_enums.Status.STORAGE


def test_delete_grading_record_keeps_sold_item_closed(
    db_session: Session,
    item_factory: ItemFactory,
    submission_factory: SubmissionFactory,
    grading_record_factory: GradingRecordFactory,
) -> None:
    item = item_factory.get(
        idx=1,
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.AUCTION,
        list_price=2000.0,
        list_date=date(2026, 1, 1),
        sale_total=3000.0,
        sale_date=date(2026, 2, 1),
        shipping=500.0,
        sale_fee=300.0,
        usd_to_jpy_rate=150.0,
    )
    submission = submission_factory.get(idx=1)
    db_session.add_all([item, submission])
    db_session.flush()
    record = grading_record_factory.get(
        idx=1,
        item_id=item.id,
        submission_id=submission.id,
        grading_fee=1000,
        grade=9.0,
        cert=12345,
    )
    db_session.add(record)
    db_session.flush()

    assert crud.delete_grading_record_by_id(db_session, record.id) is True

    db_session.refresh(item)
    assert item.status == item_enums.Status.CLOSED
    assert item.sale_total == 3000.0


def test_delete_grading_record_keeps_listed_item_listed(
    db_session: Session,
    item_factory: ItemFactory,
    submission_factory: SubmissionFactory,
    grading_record_factory: GradingRecordFactory,
) -> None:
    item = item_factory.get(
        idx=1,
        status=item_enums.Status.LISTED,
        list_type=item_enums.ListingType.AUCTION,
        list_price=2000.0,
        list_date=date(2026, 1, 1),
    )
    submission = submission_factory.get(idx=1)
    db_session.add_all([item, submission])
    db_session.flush()
    record = grading_record_factory.get(
        idx=1,
        item_id=item.id,
        submission_id=submission.id,
        grading_fee=1000,
        grade=9.0,
        cert=12345,
    )
    db_session.add(record)
    db_session.flush()

    assert crud.delete_grading_record_by_id(db_session, record.id) is True

    db_session.refresh(item)
    assert item.status == item_enums.Status.LISTED
    assert item.list_price == 2000.0


def test_create_refund_without_item(
    db_session: Session,
    refund_create_factory: RefundCreateFactory,
) -> None:
    refund = refund_create_factory.get()
    db_refund = crud.create_refund(db_session, refund)

    refund_from_db = db_session.query(models.Refund).first()
    assert db_refund.id is not None
    assert db_refund == refund_from_db
    assert db_refund.item_id is None
    assert db_refund.refund_amount_usd == 100.0
    assert db_refund.refund_amount_jpy == 15000


def test_create_refund_linked_to_item(
    db_session: Session,
    item_factory: ItemFactory,
    refund_create_factory: RefundCreateFactory,
) -> None:
    item = item_factory.get(idx=1)
    db_session.add(item)
    db_session.flush()

    db_refund = crud.create_refund(db_session, refund_create_factory.get(item_id=item.id))
    assert db_refund.item_id == item.id
    assert db_refund.item == item


def test_get_refund_returns_correct_refund(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refunds = [refund_factory.get(idx=i, refund_amount_usd=float(i)) for i in (1, 2)]
    db_session.add_all(refunds)
    db_session.flush()

    result = crud.get_refund(db_session, refunds[-1].id)
    assert result == refunds[-1]


def test_get_refund_no_refund(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    assert crud.get_refund(db_session, refund.id + 1) is None


def test_get_newest_refunds_orders_by_date_descending(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund_dates = [date(2026, 1, 1), date(2026, 3, 1), date(2026, 2, 1)]
    refunds = [refund_factory.get(idx=i, refund_date=d) for i, d in enumerate(refund_dates)]
    db_session.add_all(refunds)
    db_session.flush()

    result = crud.get_newest_refunds(db_session)
    assert [r.refund_date for r in result] == sorted(refund_dates)


def test_get_newest_refunds_skip_and_limit(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund_dates = [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1)]
    refunds = [refund_factory.get(idx=i, refund_date=d) for i, d in enumerate(refund_dates)]
    db_session.add_all(refunds)
    db_session.flush()

    result = crud.get_newest_refunds(db_session, skip=1, limit=1)
    assert [r.refund_date for r in result] == [date(2026, 2, 1)]


def test_get_total_number_of_refunds(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refunds = [refund_factory.get(idx=i) for i in (1, 2)]
    db_session.add_all(refunds)
    db_session.flush()

    assert crud.get_total_number_of_refunds(db_session) == len(refunds)


def test_delete_refund_by_id_success(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refunds = [refund_factory.get(idx=i) for i in (1, 2)]
    ids = [r.id for r in refunds]
    db_session.add_all(refunds)
    db_session.flush()

    assert crud.delete_refund_by_id(db_session, ids[-1]) is True
    assert crud.get_refund(db_session, ids[-1]) is None
    assert crud.get_refund(db_session, ids[0]) is not None


def test_delete_refund_by_id_failure(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    assert crud.delete_refund_by_id(db_session, refund.id + 1) is False
    assert crud.get_refund(db_session, refund.id) is not None


def test_delete_refund_leaves_linked_item(
    db_session: Session,
    item_factory: ItemFactory,
    refund_factory: RefundFactory,
) -> None:
    item = item_factory.get(idx=1)
    db_session.add(item)
    db_session.flush()
    refund = refund_factory.get(idx=1, item_id=item.id)
    db_session.add(refund)
    db_session.flush()

    assert crud.delete_refund_by_id(db_session, refund.id) is True
    assert crud.get_item(db_session, item.id) is not None


def test_edit_refund_no_refund_found(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(db_session, refund_id=100, refund_update=schemas.RefundUpdate())
    assert result == 404


def test_edit_refund_no_changes(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(
        db_session,
        refund_id=refund.id,
        refund_update=schemas.RefundUpdate(),
    )
    assert result == 303
    assert crud.get_refund(db_session, refund.id) == refund


def test_edit_refund_single_field(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(
        db_session,
        refund_id=refund.id,
        refund_update=schemas.RefundUpdate(refund_amount_usd=250.0),
    )
    assert result == 303

    changed_refund = crud.get_refund(db_session, refund.id)
    assert changed_refund is not None
    assert changed_refund.refund_amount_usd == 250.0
    assert changed_refund.refund_date == date(2026, 3, 1)


def test_edit_refund_enum_field(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(
        db_session,
        refund_id=refund.id,
        refund_update=schemas.RefundUpdate(refund_reason=item_enums.RefundReason.DAMAGE),
    )
    assert result == 303

    changed_refund = crud.get_refund(db_session, refund.id)
    assert changed_refund is not None
    assert changed_refund.refund_reason == item_enums.RefundReason.DAMAGE


def test_edit_refund_multiple_changes(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(
        db_session,
        refund_id=refund.id,
        refund_update=schemas.RefundUpdate(
            refund_amount_usd=200.0,
            refund_date=date(2026, 4, 2),
            usd_to_jpy_rate=160.0,
        ),
    )
    assert result == 303

    changed_refund = crud.get_refund(db_session, refund.id)
    assert changed_refund is not None
    assert changed_refund.refund_amount_usd == 200.0
    assert changed_refund.refund_date == date(2026, 4, 2)
    assert changed_refund.refund_amount_jpy == 32000


def test_edit_refund_clears_nullable_item_id(
    db_session: Session,
    item_factory: ItemFactory,
    refund_factory: RefundFactory,
) -> None:
    item = item_factory.get(idx=1)
    db_session.add(item)
    db_session.flush()
    refund = refund_factory.get(idx=1, item_id=item.id)
    db_session.add(refund)
    db_session.flush()

    result = crud.edit_refund(
        db_session,
        refund_id=refund.id,
        refund_update=schemas.RefundUpdate(item_id=None),
    )
    assert result == 303

    changed_refund = crud.get_refund(db_session, refund.id)
    assert changed_refund is not None
    assert changed_refund.item_id is None


def test_edit_refund_rejects_cleared_required_field(
    db_session: Session,
    refund_factory: RefundFactory,
) -> None:
    refund = refund_factory.get(idx=1)
    db_session.add(refund)
    db_session.flush()

    with pytest.raises(ValueError, match='cannot be removed'):
        crud.edit_refund(
            db_session,
            refund_id=refund.id,
            refund_update=schemas.RefundUpdate(refund_amount_usd=None),
        )
