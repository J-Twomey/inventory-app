from datetime import date

from sqlalchemy import (
    Boolean,
    case,
    cast,
    Date,
    Enum as SQLAlchemyEnum,
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
    Language,
    Qualifier,
    Status,
    Intent,
    GradingCompany,
    ListingType,
    ObjectVariant,
)


NullableDate = Mapped[date | None]
NullableFloat = Mapped[float | None]
NullableInt = Mapped[int | None]


def NullableDateColumn(**kwargs) -> NullableDate:
    return mapped_column(Date, nullable=True, **kwargs)


def NullableFloatColumn(**kwargs) -> NullableFloat:
    return mapped_column(Float, nullable=True, **kwargs)


def NullableIntColumn(**kwargs) -> NullableInt:
    return mapped_column(Integer, nullable=True, **kwargs)


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    set_name: Mapped[str] = mapped_column(String)
    category: Mapped[Category] = mapped_column(SQLAlchemyEnum(Category))
    language: Mapped[Language] = mapped_column(SQLAlchemyEnum(Language))
    qualifiers: Mapped[list[Qualifier] | None] = mapped_column(EnumList(Qualifier))
    details: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_date: Mapped[date] = mapped_column(Date)
    purchase_price: Mapped[int] = mapped_column(Integer)
    status: Mapped[Status] = mapped_column(SQLAlchemyEnum(Status))
    intent: Mapped[Intent] = mapped_column(SQLAlchemyEnum(Intent))
    grading_fee: Mapped[dict[int, int]] = mapped_column(JSON)
    grading_fee_total: Mapped[int] = mapped_column(Integer)
    grade: NullableFloat = NullableFloatColumn()
    grading_company: Mapped[GradingCompany] = mapped_column(SQLAlchemyEnum(GradingCompany))
    cert: NullableInt = NullableIntColumn()
    submission_number: Mapped[list[int]] = mapped_column(JSON)
    list_price: NullableFloat = NullableFloatColumn()
    list_type: Mapped[ListingType] = mapped_column(SQLAlchemyEnum(ListingType))
    list_date: NullableDate = NullableDateColumn()
    sale_total: NullableFloat = NullableFloatColumn()
    sale_date: NullableDate = NullableDateColumn()
    shipping: NullableFloat = NullableFloatColumn()
    sale_fee: NullableFloat = NullableFloatColumn()
    usd_to_jpy_rate: NullableFloat = NullableFloatColumn()
    group_discount: Mapped[bool] = mapped_column(Boolean)
    object_variant: Mapped[ObjectVariant] = mapped_column(SQLAlchemyEnum(ObjectVariant))
    audit_target: Mapped[bool] = mapped_column(Boolean)

    @hybrid_property
    def total_cost(self) -> int:
        return self.purchase_price + self.grading_fee_total

    @total_cost.expression  # type: ignore[no-redef]
    def total_cost(cls) -> BinaryExpression:
        return cls.purchase_price + cls.grading_fee_total

    @hybrid_property
    def total_fees(self) -> float | None:
        if self.shipping is None or self.sale_fee is None:
            return None
        else:
            return self.shipping + self.sale_fee

    @total_fees.expression  # type: ignore[no-redef]
    def total_fees(cls) -> ColumnElement[float | None]:
        return case(
            (
                (cls.shipping.is_not(None)) & (cls.sale_fee.is_not(None)),
                cls.shipping + cls.sale_fee,
            ),
            else_=null(),
        )

    @hybrid_property
    def return_usd(self) -> float | None:
        if self.sale_total is None or self.total_fees is None:
            return None
        else:
            return self.sale_total - self.total_fees

    @return_usd.expression  # type: ignore[no-redef]
    def return_usd(cls) -> ColumnElement[float | None]:
        return case(
            (
                (cls.sale_total.is_not(None)) & (cls.total_fees.is_not(None)),
                cls.sale_total - cls.total_fees,
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
            else_=null(),  # avoid zero division
        )
