from datetime import date

from sqlalchemy import (
    Boolean,
    case,
    cast,
    Date,
    Float,
    ForeignKey,
    func,
    Integer,
    literal,
    null,
    select,
    String,
    true,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
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
from .schemas import (
    GradingRecordDisplay,
    ItemDisplay,
    SubmissionDisplay,
)


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
    import_fee: Mapped[int] = mapped_column(Integer)
    purchase_grading_company: Mapped[int] = mapped_column(Integer)
    purchase_cert: NullableInt = NullableIntColumn()
    purchase_grade: NullableFloat = NullableFloatColumn()
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
    cracked_from_purchase: Mapped[bool] = mapped_column(Boolean)

    submissions: Mapped[list['GradingRecord']] = relationship(
        back_populates='original_item',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    @hybrid_property
    def total_grading_fees(self) -> int:
        return sum(sub.grading_fee for sub in self.submissions if sub.grading_fee is not None)

    @total_grading_fees.expression  # type: ignore[no-redef]
    def total_grading_fees(cls) -> BinaryExpression[int]:
        return (
            select(func.sum(GradingRecord.grading_fee))
            .where(GradingRecord.item_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def total_cost(self) -> int:
        return self.purchase_price + self.total_grading_fees + self.import_fee

    @total_cost.expression  # type: ignore[no-redef]
    def total_cost(cls) -> BinaryExpression[int]:
        return cls.purchase_price + cls.total_grading_fees + cls.import_fee

    @hybrid_property
    def grading_company(self) -> int:
        latest_submission = max(
            self.submissions,
            key=lambda s: s.submission_number,
            default=None,
        )
        if latest_submission is None:
            if self.cracked_from_purchase:
                return GradingCompany.RAW.value
            else:
                return self.purchase_grading_company
        else:
            if latest_submission.is_cracked:
                return GradingCompany.RAW.value
            else:
                return latest_submission.submission.submission_company

    @grading_company.expression  # type: ignore[no-redef]
    def grading_company(cls):
        latest_company = (
            select(GradingRecord.submission_company)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_cracked = (
            select(GradingRecord.is_cracked)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        return case(
            (
                latest_company.is_(None),
                case(
                    (cls.cracked_from_purchase.is_(true()), literal(GradingCompany.RAW.value)),
                    else_=cls.purchase_grading_company,
                ),
            ),
            else_=case(
                (latest_cracked.is_(true()), literal(GradingCompany.RAW.value)),
                else_=latest_company,
            ),
        )

    @hybrid_property
    def cert(self) -> int | None:
        latest_submission = max(
            self.submissions,
            key=lambda s: s.submission_number,
            default=None,
        )
        if latest_submission is None:
            if self.cracked_from_purchase:
                return None
            else:
                return self.purchase_cert
        else:
            if latest_submission.is_cracked:
                return None
            else:
                return latest_submission.cert

    @cert.expression  # type: ignore[no-redef]
    def cert(cls) -> ColumnElement[int | None]:
        latest_cert = (
            select(GradingRecord.cert)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_cracked = (
            select(GradingRecord.is_cracked)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        return case(
            (
                latest_cert.is_(None),
                case(
                    (cls.cracked_from_purchase.is_(true()), literal(None, type_=Integer())),
                    else_=cls.purchase_cert,
                ),
            ),
            else_=case(
                (latest_cracked.is_(true()), literal(None, type_=Integer())),
                else_=latest_cert,
            ),
        )

    @hybrid_property
    def grade(self) -> float | None:
        latest_submission = max(
            self.submissions,
            key=lambda s: s.submission_number,
            default=None,
        )
        if latest_submission is None:
            if self.cracked_from_purchase:
                return None
            else:
                return self.purchase_grade
        else:
            if latest_submission.is_cracked:
                return None
            else:
                return latest_submission.grade

    @grade.expression  # type: ignore[no-redef]
    def grade(cls) -> ColumnElement[float | None]:
        latest_grade = (
            select(GradingRecord.grade)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_cracked = (
            select(GradingRecord.is_cracked)
            .where(GradingRecord.item_id == cls.id)
            .order_by(GradingRecord.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        return case(
            (
                latest_grade.is_(None),
                case(
                    (cls.cracked_from_purchase.is_(true()), literal(None, type_=Float())),
                    else_=cls.purchase_grade,
                ),
            ),
            else_=case(
                (latest_cracked.is_(true()), literal(None, type_=Float())),
                else_=latest_grade,
            ),
        )

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

    def to_display(self) -> ItemDisplay:
        return ItemDisplay(
            id=self.id,
            name=self.name,
            set_name=self.set_name,
            category=Category(self.category).name.title(),
            language=Language(self.language).name.title().replace('_', ' '),
            qualifiers=[q.name.title().replace('_', ' ') for q in self.qualifiers],
            details=self.details,
            purchase_date=self.purchase_date,
            purchase_price=self.purchase_price,
            status=Status(self.status).name.title(),
            intent=Intent(self.intent).name.title(),
            import_fee=self.import_fee,
            grading_company=GradingCompany(self.grading_company).name,
            list_price=self.list_price,
            list_type=ListingType(self.list_type).name.title().replace('_', ' '),
            list_date=self.list_date,
            sale_total=self.sale_total,
            sale_date=self.sale_date,
            shipping=self.shipping,
            sale_fee=self.sale_fee,
            usd_to_jpy_rate=self.usd_to_jpy_rate,
            group_discount=self.group_discount,
            object_variant=ObjectVariant(self.object_variant).name.title().replace('_', ' '),
            audit_target=self.audit_target,
            total_grading_fees=self.total_grading_fees,
            total_cost=self.total_cost,
            grade=self.grade,
            cert=self.cert,
            total_fees=self.total_fees,
            return_usd=self.return_usd,
            return_jpy=self.return_jpy,
            net_jpy=self.net_jpy,
            net_percent=self.net_percent,
        )


class Submission(Base):
    __tablename__ = 'submission'

    submission_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_company: Mapped[int] = mapped_column(Integer)
    submission_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    break_even_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    submission_items: Mapped[list['GradingRecord']] = relationship(
        back_populates='submission',
        cascade='all, delete-orphan',
        passive_deletes=True,
    )

    @hybrid_property
    def card_cost(self) -> int:
        return sum(
            [
                item.original_item.purchase_price + item.original_item.import_fee
                for item in self.submission_items
            ]
        )

    @hybrid_property
    def grading_cost(self) -> int:
        grading_fees = [item.grading_fee for item in self.submission_items]
        return sum(grading_fees)

    @hybrid_property
    def total_cost(self) -> int:
        return self.card_cost + self.grading_cost

    @hybrid_property
    def total_return(self) -> int:
        return_values = [
            item.original_item.return_jpy
            for item in self.submission_items if item.original_item.return_jpy is not None
        ]
        return sum(return_values)

    @hybrid_property
    def total_profit(self) -> int:
        return self.total_return - self.total_cost

    @hybrid_property
    def profit_on_sold(self) -> int:
        profits = [
            item.original_item.return_jpy -
            item.original_item.purchase_price -
            item.original_item.import_fee -
            item.grading_fee
            for item in self.submission_items if item.original_item.return_jpy is not None
        ]
        return sum(profits)

    @hybrid_property
    def num_cards(self) -> int:
        return len(self.submission_items)

    @hybrid_property
    def num_sold(self) -> int:
        sold_items = [
            item for item in self.submission_items if item.original_item.return_jpy is not None
        ]
        return len(sold_items)

    @hybrid_property
    def percent_sold(self) -> float:
        return round(100 * self.num_sold / self.num_cards, 2)

    @hybrid_property
    def profit_per_sold(self) -> int:
        if self.num_sold == 0:
            return 0
        return round(self.profit_on_sold / self.num_sold)

    @hybrid_property
    def num_closed(self) -> int:
        sold_or_cracked_items = [
            item for item in self.submission_items
            if (item.original_item.return_jpy is not None) or item.is_cracked
        ]
        return len(sold_or_cracked_items)

    @hybrid_property
    def percent_closed(self) -> float:
        return round(100 * self.num_closed / self.num_cards, 2)

    @hybrid_property
    def profit_per_closed(self) -> int:
        if self.num_closed == 0:
            return 0
        return round(self.profit_on_sold / self.num_closed)

    def to_display(self) -> SubmissionDisplay:
        return SubmissionDisplay(
            submission_number=self.submission_number,
            submission_company=GradingCompany(self.submission_company).name,
            submission_date=self.submission_date,
            return_date=self.return_date,
            break_even_date=self.break_even_date,
            card_cost=self.card_cost,
            grading_cost=self.grading_cost,
            total_cost=self.total_cost,
            total_return=self.total_return,
            total_profit=self.total_profit,
            profit_on_sold=self.profit_on_sold,
            num_cards=self.num_cards,
            num_sold=self.num_sold,
            percent_sold=self.percent_sold,
            profit_per_sold=self.profit_per_sold,
            num_closed=self.num_closed,
            percent_closed=self.percent_closed,
            profit_per_closed=self.profit_per_closed,
        )


class GradingRecord(Base):
    __tablename__ = 'grading_record'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey('items.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    submission_number: Mapped[int] = mapped_column(
        ForeignKey('submission.submission_number', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    grading_fee: Mapped[int] = mapped_column(Integer)
    grade: NullableInt = NullableIntColumn()
    cert: NullableInt = NullableIntColumn()
    is_cracked: Mapped[bool] = mapped_column(Boolean)

    submission: Mapped[Submission] = relationship(back_populates='submission_items')
    original_item: Mapped[Item] = relationship(
        back_populates='submissions',
    )

    @hybrid_property
    def submission_company(self) -> int:
        return self.submission.submission_company

    @submission_company.expression  # type: ignore[no-redef]
    def submission_company(cls):
        return (
            select(Submission.submission_company)
            .where(Submission.submission_number == cls.submission_number)
            .scalar_subquery()
        )

    def to_display(self) -> GradingRecordDisplay:
        return GradingRecordDisplay(
            id=self.id,
            item_id=self.item_id,
            submission_number=self.submission_number,
            grading_fee=self.grading_fee,
            grade=self.grade,
            cert=self.cert,
            is_cracked=self.is_cracked,
            name=self.original_item.name,
            set_name=self.original_item.set_name,
            language=Language(self.original_item.language).name.title().replace('_', ' '),
            category=Category(self.original_item.category).name.title(),
            purchase_price=self.original_item.purchase_price,
            import_fee=self.original_item.import_fee,
            return_jpy=self.original_item.return_jpy,
        )
