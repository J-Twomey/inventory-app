from datetime import date
from typing import (
    Any,
    Callable,
    Generator,
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

import src.item_enums as item_enums
from main import app
from src.database import (
    Base,
    get_db,
)
from src.models import (
    GradingRecord,
    Item,
    Submission,
)
from src.schemas import (
    ItemBase,
    ItemCreate,
)


TEST_DATABASE_URL = 'sqlite:///:memory:'


@pytest.fixture(scope='session')
def engine() -> Generator[Engine, None, None]:
    engine = create_engine(TEST_DATABASE_URL, connect_args={'check_same_thread': False})
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(engine: Engine) -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as cl:
        yield cl


class ItemFactory:
    def get(
        self,
        id: int = 1,
        name: str = 'TESTER',
        set_name: str = 'Base Set',
        category: int = item_enums.Category.CARD.value,
        language: int = item_enums.Language.KOREAN.value,
        qualifiers: list[item_enums.Qualifier] | None = None,
        details: str | None = None,
        purchase_date: date = date(2025, 5, 5),
        purchase_price: int = 1000,
        status: int = item_enums.Status.STORAGE.value,
        intent: int = item_enums.Intent.SELL.value,
        import_fee: int = 0,
        purchase_grading_company: int = item_enums.GradingCompany.RAW.value,
        purchase_grade: float | None = None,
        purchase_cert: float | None = None,
        list_price: float | None = None,
        list_type: int = item_enums.ListingType.NO_LIST.value,
        list_date: date | None = None,
        sale_total: float | None = None,
        sale_date: date | None = None,
        shipping: float | None = None,
        sale_fee: float | None = None,
        usd_to_jpy_rate: float | None = None,
        group_discount: bool = False,
        object_variant: int = item_enums.ObjectVariant.STANDARD.value,
        audit_target: bool = False,
        cracked_from_purchase: bool = False,
    ) -> Item:
        if qualifiers is None:
            qualifiers = []
        return Item(
            id=id,
            name=name,
            set_name=set_name,
            category=category,
            language=language,
            qualifiers=qualifiers,
            details=details,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            status=status,
            intent=intent,
            import_fee=import_fee,
            purchase_grading_company=purchase_grading_company,
            purchase_grade=purchase_grade,
            purchase_cert=purchase_cert,
            list_price=list_price,
            list_type=list_type,
            list_date=list_date,
            sale_total=sale_total,
            sale_date=sale_date,
            shipping=shipping,
            sale_fee=sale_fee,
            usd_to_jpy_rate=usd_to_jpy_rate,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
            cracked_from_purchase=cracked_from_purchase,
        )


@pytest.fixture(scope='function')
def item_factory() -> ItemFactory:
    return ItemFactory()


class ItemBaseFactory:
    def get(
        self,
        name: str = 'TESTER',
        set_name: str = 'Base Set',
        category: item_enums.Category = item_enums.Category.CARD,
        language: item_enums.Language = item_enums.Language.KOREAN,
        qualifiers: list[item_enums.Qualifier] | None = None,
        details: str | None = None,
        purchase_date: date = date(2025, 5, 5),
        purchase_price: int = 1000,
        status: item_enums.Status = item_enums.Status.STORAGE,
        intent: item_enums.Intent = item_enums.Intent.SELL,
        import_fee: int = 0,
        purchase_grading_company: item_enums.GradingCompany = item_enums.GradingCompany.RAW,
        purchase_grade: float | None = None,
        purchase_cert: int | None = None,
        list_price: float | None = None,
        list_type: item_enums.ListingType = item_enums.ListingType.NO_LIST,
        list_date: date | None = None,
        sale_total: float | None = None,
        sale_date: date | None = None,
        shipping: float | None = None,
        sale_fee: float | None = None,
        usd_to_jpy_rate: float | None = None,
        group_discount: bool = False,
        object_variant: item_enums.ObjectVariant = item_enums.ObjectVariant.STANDARD,
        audit_target: bool = False,
        cracked_from_purchase: bool = False,
    ) -> ItemBase:
        if qualifiers is None:
            qualifiers = []
        return ItemBase(
            name=name,
            set_name=set_name,
            category=category,
            language=language,
            qualifiers=qualifiers,
            details=details,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            status=status,
            intent=intent,
            import_fee=import_fee,
            purchase_grading_company=purchase_grading_company,
            purchase_grade=purchase_grade,
            purchase_cert=purchase_cert,
            list_price=list_price,
            list_type=list_type,
            list_date=list_date,
            sale_total=sale_total,
            sale_date=sale_date,
            shipping=shipping,
            sale_fee=sale_fee,
            usd_to_jpy_rate=usd_to_jpy_rate,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
            cracked_from_purchase=cracked_from_purchase,
        )


@pytest.fixture(scope='function')
def item_base_factory() -> ItemBaseFactory:
    return ItemBaseFactory()


class ItemCreateFactory:
    def get(
        self,
        name: str = 'TESTER',
        set_name: str = 'Base Set',
        category: item_enums.Category = item_enums.Category.CARD,
        language: item_enums.Language = item_enums.Language.KOREAN,
        qualifiers: list[item_enums.Qualifier] | None = None,
        details: str | None = None,
        purchase_date: date = date(2025, 5, 5),
        purchase_price: int = 1000,
        status: item_enums.Status = item_enums.Status.STORAGE,
        intent: item_enums.Intent = item_enums.Intent.SELL,
        import_fee: int = 0,
        purchase_grading_company: item_enums.GradingCompany = item_enums.GradingCompany.RAW,
        purchase_grade: float | None = None,
        purchase_cert: int | None = None,
        list_price: float | None = None,
        list_type: item_enums.ListingType = item_enums.ListingType.NO_LIST,
        list_date: date | None = None,
        sale_total: float | None = None,
        sale_date: date | None = None,
        shipping: float | None = None,
        sale_fee: float | None = None,
        usd_to_jpy_rate: float | None = None,
        group_discount: bool = False,
        object_variant: item_enums.ObjectVariant = item_enums.ObjectVariant.STANDARD,
        audit_target: bool = False,
        cracked_from_purchase: bool = False,
    ) -> ItemCreate:
        if qualifiers is None:
            qualifiers = []
        return ItemCreate(
            name=name,
            set_name=set_name,
            category=category,
            language=language,
            qualifiers=qualifiers,
            details=details,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            status=status,
            intent=intent,
            import_fee=import_fee,
            purchase_grading_company=purchase_grading_company,
            purchase_grade=purchase_grade,
            purchase_cert=purchase_cert,
            list_price=list_price,
            list_type=list_type,
            list_date=list_date,
            sale_total=sale_total,
            sale_date=sale_date,
            shipping=shipping,
            sale_fee=sale_fee,
            usd_to_jpy_rate=usd_to_jpy_rate,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
            cracked_from_purchase=cracked_from_purchase,
        )


@pytest.fixture(scope='function')
def item_create_factory() -> ItemCreateFactory:
    return ItemCreateFactory()


class GradingRecordFactory:
    def get(
        self,
        id: int = 1,
        item_id: int = 100,
        submission_number: int = 1,
        grading_fee: int | None = None,
        grade: float | None = None,
        cert: int | None = None,
        is_cracked: bool = False,
    ) -> GradingRecord:
        return GradingRecord(
            id=id,
            item_id=item_id,
            submission_number=submission_number,
            grading_fee=grading_fee,
            grade=grade,
            cert=cert,
            is_cracked=is_cracked,
        )


@pytest.fixture(scope='function')
def grading_record_factory() -> GradingRecordFactory:
    return GradingRecordFactory()


class SubmissionFactory:
    def get(
        self,
        submission_number: int = 1,
        submission_company: int = 1,
        submission_date: date | None = None,
        return_date: date | None = None,
        break_even_date: date | None = None,
    ) -> Submission:
        return Submission(
            submission_number=submission_number,
            submission_company=submission_company,
            submission_date=submission_date,
            return_date=return_date,
            break_even_date=break_even_date,
        )


@pytest.fixture(scope='function')
def submission_factory() -> SubmissionFactory:
    return SubmissionFactory()


@pytest.fixture(scope='function')
def item_with_submissions_factory(
        db_session: Session,
        item_factory: ItemFactory,
        grading_record_factory: GradingRecordFactory,
        submission_factory: SubmissionFactory,
) -> Callable[[Any], Item]:
    def get(
        grading_record_ids: list[int] | None = None,
        submission_numbers: list[int] | None = None,
        submission_companies: list[int] | None = None,
        submission_dates: list[date | None] | None = None,
        grading_fees: list[int] | None = None,
        grades: list[float] | None = None,
        certs: list[int] | None = None,
        is_cracked_flags: list[bool] | None = None,
        return_dates: list[date | None] | None = None,
        break_even_dates: list[date | None] | None = None,
        **item_kwargs: Any,
    ) -> Item:
        grading_record_ids_ = grading_record_ids or [1]
        submission_numbers_ = submission_numbers or [1]
        submission_companies_ = submission_companies or len(grading_record_ids_) * [1]
        submission_dates_ = submission_dates or len(grading_record_ids_) * [None]
        grading_fees_ = grading_fees or len(grading_record_ids_) * [None]
        grades_ = grades or len(grading_record_ids_) * [None]
        certs_ = certs or len(grading_record_ids_) * [None]
        is_cracked_flags_ = is_cracked_flags or len(grading_record_ids_) * [False]
        return_dates_ = return_dates or len(grading_record_ids_) * [None]
        break_even_dates_ = break_even_dates or len(grading_record_ids_) * [None]

        # input validation
        input_lists = [
            grading_record_ids_,
            submission_numbers_,
            submission_companies_,
            submission_dates_,
            grading_fees_,
            grades_,
            certs_,
            is_cracked_flags_,
            return_dates_,
            break_even_dates_,
        ]
        assert len({len(lst) for lst in input_lists}) == 1

        sub_nums_indices_map: dict[int, list[int]] = {}
        for i, sub_num in enumerate(submission_numbers_):
            if sub_num not in sub_nums_indices_map:
                sub_nums_indices_map[sub_num] = []
            sub_nums_indices_map[sub_num].append(i)

        for sub_num, sub_indices in sub_nums_indices_map.items():
            # input validation
            sub_companies = [submission_companies_[i] for i in sub_indices]
            assert len(set(sub_companies)) == 1
            sub_submit_dates = [submission_dates_[i] for i in sub_indices]
            assert len(set(sub_submit_dates)) == 1
            sub_return_dates = [return_dates_[i] for i in sub_indices]
            assert len(set(sub_return_dates)) == 1
            sub_break_even_dates = [break_even_dates_[i] for i in sub_indices]
            assert len(set(sub_break_even_dates)) == 1
            submission = submission_factory.get(
                submission_number=sub_num,
                submission_company=sub_companies[0],
                submission_date=sub_submit_dates[0],
                return_date=sub_return_dates[0],
                break_even_date=sub_break_even_dates[0],
            )
            db_session.add(submission)

        item = item_factory.get(**item_kwargs)
        db_session.add(item)
        db_session.flush()
        records = [
            grading_record_factory.get(
                id=grading_record_ids_[i],
                item_id=item.id,
                submission_number=submission_numbers_[i],
                grading_fee=grading_fees_[i],
                grade=grades_[i],
                cert=certs_[i],
                is_cracked=is_cracked_flags_[i],
            )
            for i in range(len(grading_record_ids_))
        ]
        if len(records) > 0:
            db_session.add_all(records)

        db_session.commit()
        db_session.refresh(item)
        return item
    return get
