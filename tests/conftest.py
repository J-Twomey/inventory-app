from datetime import date
from typing import Generator

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
from src.models import Item
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
        grading_fee: dict[int, int] | None = None,
        cracked_from: list[int] | None = None,
        grade: float | None = None,
        grading_company: int = item_enums.GradingCompany.RAW.value,
        cert: float | None = None,
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
    ) -> Item:
        if qualifiers is None:
            qualifiers = []
        if grading_fee is None:
            grading_fee = {}
        if cracked_from is None:
            cracked_from = []
        submission_numbers = list(grading_fee)
        grading_fee_total = sum(grading_fee.values())
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
            grading_fee=grading_fee,
            grading_fee_total=grading_fee_total,
            submission_numbers=submission_numbers,
            cracked_from=cracked_from,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
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
        grading_fee: dict[int, int] | None = None,
        cracked_from: list[int] | None = None,
        grade: float | None = None,
        grading_company: item_enums.GradingCompany = item_enums.GradingCompany.RAW,
        cert: int | None = None,
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
    ) -> ItemBase:
        if qualifiers is None:
            qualifiers = []
        if grading_fee is None:
            grading_fee = {}
        if cracked_from is None:
            cracked_from = []
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
            grading_fee=grading_fee,
            cracked_from=cracked_from,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
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
        grading_fee: dict[int, int] | None = None,
        cracked_from: list[int] | None = None,
        grade: float | None = None,
        grading_company: item_enums.GradingCompany = item_enums.GradingCompany.RAW,
        cert: int | None = None,
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
    ) -> ItemCreate:
        if qualifiers is None:
            qualifiers = []
        if grading_fee is None:
            grading_fee = {}
        if cracked_from is None:
            cracked_from = []
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
            grading_fee=grading_fee,
            cracked_from=cracked_from,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
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
        )


@pytest.fixture(scope='function')
def item_create_factory() -> ItemCreateFactory:
    return ItemCreateFactory()
