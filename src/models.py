from datetime import date

from sqlalchemy import (
    Boolean,
    case,
    cast,
    Date,
    Float,
    func,
    Integer,
    JSON,
    null,
    String,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from sqlalchemy.sql.elements import (
    BinaryExpression,
    ColumnElement,
)

from .database import Base
from .item_enums import (
    Category,
    EnumList,
    GradingCompany,
    Intent,
    Language,
    ListingType,
    ObjectVariant,
    Qualifier,
    Status,
)
from .schemas import DisplayItem


NullableDate = Mapped[date | None]
NullableFloat = Mapped[float | None]
NullableInt = Mapped[int | None]


def NullableDateColumn() -> NullableDate:
    return mapped_column(Date, nullable=True)


def NullableFloatColumn() -> NullableFloat:
    return mapped_column(Float, nullable=True)


def NullableIntColumn() -> NullableInt:
    return mapped_column(Integer, nullable=True)


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    set_name: Mapped[str] = mapped_column(String)
    category: Mapped[int] = mapped_column(Integer)
    language: Mapped[int] = mapped_column(Integer)
    qualifiers: Mapped[list[Qualifier]] = mapped_column(EnumList(Qualifier))
    details: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date)
    purchase_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[int] = mapped_column(Integer)
    intent: Mapped[int] = mapped_column(Integer)
    grading_fee: Mapped[dict[int, int]] = mapped_column(JSON)
    grading_fee_total: Mapped[int] = mapped_column(Integer)
    submission_numbers: Mapped[list[int]] = mapped_column(JSON)
    cracked_from: Mapped[list[int]] = mapped_column(JSON)
    grade: NullableFloat = NullableFloatColumn()
    grading_company: Mapped[int] = mapped_column(Integer)
    cert: NullableInt = NullableIntColumn()
    list_price: NullableFloat = NullableFloatColumn()
    list_type: Mapped[int] = mapped_column(Integer)
    list_date: NullableDate = NullableDateColumn()
    sale_total: NullableFloat = NullableFloatColumn()
    sale_date: NullableDate = NullableDateColumn()
    shipping: NullableFloat = NullableFloatColumn()
    sale_fee: NullableFloat = NullableFloatColumn()
    usd_to_jpy_rate: NullableFloat = NullableFloatColumn()
    group_discount: Mapped[bool] = mapped_column(Boolean)
    object_variant: Mapped[int] = mapped_column(Integer)
    audit_target: Mapped[bool] = mapped_column(Boolean)

    @hybrid_property
    def total_cost(self) -> int:
        return self.purchase_price + self.grading_fee_total

    @total_cost.expression  # type: ignore[no-redef]
    def total_cost(cls) -> BinaryExpression[int]:
        return cls.purchase_price + cls.grading_fee_total

    @hybrid_property
    def total_fees(self) -> float | None:
        if self.shipping is None or self.sale_fee is None:
            return None
        else:
            return round(self.shipping + self.sale_fee, 2)

    @total_fees.expression  # type: ignore[no-redef]
    def total_fees(cls) -> ColumnElement[float | None]:
        return case(
            (
                (cls.shipping.is_not(None)) & (cls.sale_fee.is_not(None)),
                func.round(cls.shipping + cls.sale_fee, 2),
            ),
            else_=null(),
        )

    @hybrid_property
    def return_usd(self) -> float | None:
        if self.sale_total is None or self.total_fees is None:
            return None
        else:
            return round(self.sale_total - self.total_fees, 2)

    @return_usd.expression  # type: ignore[no-redef]
    def return_usd(cls) -> ColumnElement[float | None]:
        return case(
            (
                (cls.sale_total.is_not(None)) & (cls.total_fees.is_not(None)),
                func.round(cls.sale_total - cls.total_fees, 2),
            ),
            else_=null(),
        )

    @hybrid_property
    def return_jpy(self) -> int | None:
        if self.return_usd is None or self.usd_to_jpy_rate is None:
            return None
        else:
            return round(self.return_usd * self.usd_to_jpy_rate)

    @return_jpy.expression  # type: ignore[no-redef]
    def return_jpy(cls) -> ColumnElement[int | None]:
        return case(
            (
                (cls.return_usd.is_not(None)) & (cls.usd_to_jpy_rate.is_not(None)),
                cast(func.round(cls.return_usd * cls.usd_to_jpy_rate, 0), Integer),
            ),
            else_=null(),
        )

    @hybrid_property
    def net_jpy(self) -> int | None:
        if self.return_jpy is None:
            return None
        else:
            return round(self.return_jpy - self.total_cost)

    @net_jpy.expression  # type: ignore[no-redef]
    def net_jpy(cls) -> ColumnElement[int | None]:
        return case(
            (
                cls.return_jpy.is_not(None),
                cast(func.round(cls.return_jpy - cls.total_cost, 0), Integer),
            ),
            else_=null(),
        )

    @hybrid_property
    def net_percent(self) -> float | None:
        if self.net_jpy is None:
            return None
        elif self.total_cost == 0:
            return 0.
        else:
            return round(100 * self.net_jpy / self.total_cost, 2)

    @net_percent.expression  # type: ignore[no-redef]
    def net_percent(cls) -> ColumnElement[float | None]:
        return case(
            (
                cls.net_jpy.is_(None),
                null(),
            ),
            (
                cls.total_cost != 0,
                func.round(cls.net_jpy / cls.total_cost, 2),
            ),
            else_=0.,
        )

    def to_display(self) -> DisplayItem:
        return DisplayItem(
            id=self.id,
            name=self.name,
            set_name=self.set_name,
            category=Category(self.category),
            language=Language(self.language),
            qualifiers=self.qualifiers,
            details=self.details,
            purchase_date=self.purchase_date,
            purchase_price=self.purchase_price,
            status=Status(self.status),
            intent=Intent(self.intent),
            grading_fee=self.grading_fee,
            grading_fee_total=self.grading_fee_total,
            submission_numbers=self.submission_numbers,
            cracked_from=self.cracked_from,
            grade=self.grade,
            grading_company=GradingCompany(self.grading_company),
            cert=self.cert,
            list_price=self.list_price,
            list_type=ListingType(self.list_type),
            list_date=self.list_date,
            sale_total=self.sale_total,
            sale_date=self.sale_date,
            shipping=self.shipping,
            sale_fee=self.sale_fee,
            usd_to_jpy_rate=self.usd_to_jpy_rate,
            group_discount=self.group_discount,
            object_variant=ObjectVariant(self.object_variant),
            audit_target=self.audit_target,
            total_cost=self.total_cost,
            total_fees=self.total_fees,
            return_usd=self.return_usd,
            return_jpy=self.return_jpy,
            net_jpy=self.net_jpy,
            net_percent=self.net_percent,
        )
