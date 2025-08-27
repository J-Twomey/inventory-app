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
    null,
    select,
    String,
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
from .schemas import ItemDisplay


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
    # grading_fee: Mapped[dict[int, int]] = mapped_column(JSON)
    # grading_fee_total: Mapped[int] = mapped_column(Integer)
    # submission_numbers: Mapped[list[int]] = mapped_column(JSON)
    # cracked_from: Mapped[list[int]] = mapped_column(JSON)
    # grade: NullableFloat = NullableFloatColumn()
    grading_company: Mapped[int] = mapped_column(Integer)
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

    submissions: Mapped[list['ItemSubmission']] = relationship(
        back_populates='original_item',
        cascade='all, delete-orphan'
    )

    @hybrid_property
    def total_grading_fees(self) -> int:
        return sum(sub.grading_fee for sub in self.submissions if sub.grading_fee is not None)

    @total_grading_fees.expression  # type: ignore[no-redef]
    def total_grading_fees(cls) -> BinaryExpression[int]:
        return (
            select(func.sum(ItemSubmission.grading_fee))
            .where(ItemSubmission.item_id == cls.id)
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
    def grade(self) -> int | None:
        '''
        If a submission exists then take the newest grade from there (unless cracked), otherwise
        check if a purchase_grade exists (meaning the card was bought already graded)
        '''
        latest_submission = max(
            self.submissions,
            key=lambda s: s.submission_number,
            default=None
        )
        if latest_submission is not None and not latest_submission.is_cracked:
            return latest_submission.grade
        else:
            return self.purchase_grade

    @grade.expression  # type: ignore[no-redef]
    def grade(cls) -> ColumnElement[int | None]:
        latest_subquery = (
            select(ItemSubmission.grade, ItemSubmission.is_cracked)
            .where(ItemSubmission.item_id == cls.id)
            .order_by(ItemSubmission.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        return func.coalesce(
            case(
                (latest_subquery.c.is_cracked == True, cls.purchase_grade),
                else_=latest_subquery.c.grade
            ),
            cls.purchase_grade
        )

    @hybrid_property
    def cert(self) -> int | None:
        '''
        If a submission exists then take the newest cert from there (unless cracked), otherwise
        check if a purchase_cert exists (meaning the card was bought already graded)
        '''
        latest_submission = max(
            self.submissions,
            key=lambda s: s.submission_number,
            default=None
        )
        if latest_submission is not None and not latest_submission.is_cracked:
            return latest_submission.cert
        else:
            return self.purchase_cert

    @cert.expression  # type: ignore[no-redef]
    def cert(cls) -> ColumnElement[int | None]:
        latest_subquery = (
            select(ItemSubmission.cert, ItemSubmission.is_cracked)
            .where(ItemSubmission.item_id == cls.id)
            .order_by(ItemSubmission.submission_number.desc())
            .limit(1)
            .scalar_subquery()
        )
        return func.coalesce(
            case(
                (latest_subquery.c.is_cracked == True, cls.purchase_cert),
                else_=latest_subquery.c.cert
            ),
            cls.purchase_cert
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
            category=Category(self.category),
            language=Language(self.language),
            qualifiers=self.qualifiers,
            details=self.details,
            purchase_date=self.purchase_date,
            purchase_price=self.purchase_price,
            status=Status(self.status),
            intent=Intent(self.intent),
            import_fee=self.import_fee,
            grading_company=GradingCompany(self.grading_company),
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


class ItemSubmission(Base):
    __tablename__ = 'item_submission'

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('items.id'), index=True)
    grading_fee: NullableInt = NullableIntColumn()
    submission_number: Mapped[int] = mapped_column(Integer)
    grade: NullableInt = NullableIntColumn()
    cert: NullableInt = NullableIntColumn()
    is_cracked: Mapped[bool] = mapped_column(Boolean)

    original_item: Mapped[Item] = relationship(
        back_populates='submissions'
    )
