from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    date,
    datetime,
)
from typing import (
    Annotated,
    Any,
    Self,
)

from fastapi import (
    Form,
    Query,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
    ValidationInfo,
)

from .helper_types import T
from .item_enums import (
    Category,
    Language,
    Qualifier,
    Status,
    Intent,
    GradingCompany,
    ListingType,
    ObjectVariant,
)
from .parsers import (
    parse_enum,
    parse_nullable,
    parse_nullable_bool,
    parse_nullable_date,
    parse_nullable_enum,
    parse_nullable_percent,
    parse_to_qualifiers_list,
)


class ItemBase(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        from_attributes=True,
    )

    name: str | None = None
    set_name: str | None = None
    category: Category | None = None
    language: Language | None = None
    qualifiers: list[Qualifier] = field(default_factory=list)
    details: str | None = None
    purchase_date: date | None = None
    purchase_price: int | None = None
    status: Status | None = None
    intent: Intent | None = None
    import_fee: int | None = None
    purchase_grading_company: GradingCompany | None = None
    purchase_grade: float | None = None
    purchase_cert: int | None = None
    list_price: float | None = None
    list_type: ListingType | None = None
    list_date: date | None = None
    sale_total: float | None = None
    sale_date: date | None = None
    shipping: float | None = None
    sale_fee: float | None = None
    usd_to_jpy_rate: float | None = None
    group_discount: bool = False
    object_variant: ObjectVariant | None = None
    audit_target: bool = False
    cracked_from_purchase: bool = False

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(
        cls,
        v: T,
        info: ValidationInfo,
    ) -> T | None:
        # Empty string is handled differently for these fields
        if info.field_name in {
            'qualifiers',
            'group_discount',
            'audit_target',
            'cracked_from_purchase',
        }:
            return v
        if v == '':
            return None
        return v

    @field_validator('qualifiers', mode='before')
    @classmethod
    def parse_qualifiers(
        cls,
        v: Any,
    ) -> list[Qualifier]:
        if isinstance(v, str):
            return [Qualifier[x.strip()] for x in v.split(',') if x.strip()]
        elif isinstance(v, list) and all(isinstance(x, Qualifier) for x in v):
            return v
        raise ValueError('Qualifiers must be provided as str or list[Qualifier]')

    @model_validator(mode='after')
    def list_date_not_before_purchase_date(self) -> Self:
        if (
            self.list_date is not None and
            self.purchase_date is not None and
            self.list_date < self.purchase_date
        ):
            raise ValueError(
                f'Listing date cannot be before purchase date '
                f'(got listing date: {self.list_date}, purchase date: {self.purchase_date})',
            )
        return self

    @model_validator(mode='after')
    def sale_date_not_before_list_date(self) -> Self:
        if (
            self.list_date is not None and
            self.sale_date is not None and
            self.sale_date < self.list_date
        ):
            raise ValueError(
                f'Sale date cannot be before listing date '
                f'(got sale date: {self.sale_date}, listing date: {self.list_date})',
            )
        return self

    @model_validator(mode='after')
    def check_required_fields_based_on_status(self) -> Self:
        if self.status is not None:
            missing = [
                f for f in self.status.required_fields
                if getattr(self, f) is None
            ]
            if len(missing) > 0:
                raise ValueError(
                    f'Status {self.status.name} requires the following missing fields: {missing}',
                )
        return self

    @model_validator(mode='after')
    def check_required_null_fields_based_on_status(self) -> Self:
        if self.status is not None:
            not_null = [
                f for f in self.status.required_to_be_null
                if getattr(self, f) is not None
            ]
            if len(not_null) > 0:
                raise ValueError(
                    f'Status {self.status.name} requires the following fields to be null: '
                    f'{not_null}',
                )
        return self

    @model_validator(mode='after')
    def appropriate_listing_type(self) -> Self:
        if self.list_type is None:
            return self
        elif self.status == Status.LISTED or self.status == Status.CLOSED:
            if self.list_type == ListingType.NO_LIST:
                raise ValueError('Item cannot have list_type of NO_LIST if listed or sold')
        else:
            if self.list_type != ListingType.NO_LIST:
                raise ValueError(
                    'Item cannot have a list_type other than NO_LIST if not listed or sold',
                )
        return self

    @model_validator(mode='after')
    def appropriate_group_discount(self) -> Self:
        if self.group_discount and self.status != Status.CLOSED:
            raise ValueError('Group discount cannot be assigned to an unsold item')
        return self

    @model_validator(mode='after')
    def appropriate_audit_target(self) -> Self:
        if self.audit_target and (self.status == Status.CLOSED or self.status == Status.LISTED):
            raise ValueError('Item assigned as an audit target can not be listed or closed')
        return self


class ItemCreate(ItemBase):
    name: str
    set_name: str
    category: Category
    language: Language
    qualifiers: list[Qualifier]
    purchase_date: date
    purchase_price: int
    status: Status
    intent: Intent
    import_fee: int
    purchase_grading_company: GradingCompany
    list_type: ListingType
    object_variant: ObjectVariant

    def to_model_kwargs(
        self,
        exclude: set[str] = set(),
    ) -> dict[str, Any]:
        return self.model_dump(exclude=exclude)

    @model_validator(mode='after')
    def appropriate_status_based_on_intent(self) -> Self:
        if self.status not in self.intent.allowed_statuses:
            raise ValueError(
                f'Item can not have status of {self.status.name} with intent of '
                f'{self.intent.name}',
            )
        return self


@dataclass
class ItemCreateForm:
    name: str
    set_name: str
    category: str
    language: str
    details: str
    purchase_date: str
    purchase_price: str
    status: str
    intent: str
    import_fee: str
    purchase_grading_company: str
    purchase_grade: str
    purchase_cert: str
    list_price: str
    list_type: str
    list_date: str
    sale_total: str
    sale_date: str
    shipping: str
    sale_fee: str
    usd_to_jpy_rate: str
    object_variant: str
    group_discount: bool
    audit_target: bool
    cracked_from_purchase: bool
    qualifiers: list[str] = field(default_factory=list)

    @classmethod
    def as_form(
        cls,
        name: Annotated[str, Form()],
        set_name: Annotated[str, Form()],
        category: Annotated[str, Form()],
        language: Annotated[str, Form()],
        details: Annotated[str, Form()],
        purchase_date: Annotated[str, Form()],
        purchase_price: Annotated[str, Form()],
        status: Annotated[str, Form()],
        intent: Annotated[str, Form()],
        import_fee: Annotated[str, Form()],
        purchase_grading_company: Annotated[str, Form()],
        purchase_grade: Annotated[str, Form()],
        purchase_cert: Annotated[str, Form()],
        list_price: Annotated[str, Form()],
        list_type: Annotated[str, Form()],
        list_date: Annotated[str, Form()],
        sale_total: Annotated[str, Form()],
        sale_date: Annotated[str, Form()],
        shipping: Annotated[str, Form()],
        sale_fee: Annotated[str, Form()],
        usd_to_jpy_rate: Annotated[str, Form()],
        object_variant: Annotated[str, Form()],
        qualifiers: Annotated[list[str], Form(default_factory=list)],
        group_discount: Annotated[bool, Form()] = False,
        audit_target: Annotated[bool, Form()] = False,
        cracked_from_purchase: Annotated[bool, Form()] = False,
    ) -> 'ItemCreateForm':
        return cls(
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

    def to_item_create(self) -> ItemCreate:
        purchase_date_ = datetime.strptime(self.purchase_date, '%Y-%m-%d').date()
        if self.list_date == '':
            list_date_ = None
        else:
            list_date_ = datetime.strptime(self.list_date, '%Y-%m-%d').date()
        if self.sale_date == '':
            sale_date_ = None
        else:
            sale_date_ = datetime.strptime(self.sale_date, '%Y-%m-%d').date()
        return ItemCreate(
            name=self.name,
            set_name=self.set_name,
            category=parse_enum(self.category, Category),
            language=parse_enum(self.language, Language),
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date=purchase_date_,
            purchase_price=int(self.purchase_price),
            status=parse_enum(self.status, Status),
            intent=parse_enum(self.intent, Intent),
            import_fee=int(self.import_fee),
            purchase_grading_company=parse_enum(self.purchase_grading_company, GradingCompany),
            purchase_grade=parse_nullable(self.purchase_grade, float),
            purchase_cert=parse_nullable(self.purchase_cert, int),
            list_price=parse_nullable(self.list_price, float),
            list_type=parse_enum(self.list_type, ListingType),
            list_date=list_date_,
            sale_total=parse_nullable(self.sale_total, float),
            sale_date=sale_date_,
            shipping=parse_nullable(self.shipping, float),
            sale_fee=parse_nullable(self.sale_fee, float),
            usd_to_jpy_rate=parse_nullable(self.usd_to_jpy_rate, float),
            group_discount=self.group_discount,
            object_variant=parse_enum(self.object_variant, ObjectVariant),
            audit_target=self.audit_target,
            cracked_from_purchase=self.cracked_from_purchase,
        )


class ItemUpdate(ItemBase):
    def to_model_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


@dataclass
class ItemUpdateForm:
    name: str | None = None
    set_name: str | None = None
    category: str | None = None
    language: str | None = None
    details: str | None = None
    purchase_date: str | None = None
    purchase_price: str | None = None
    status: str | None = None
    intent: str | None = None
    import_fee: str | None = None
    purchase_grading_company: str | None = None
    purchase_grade: str | None = None
    purchase_cert: str | None = None
    list_price: str | None = None
    list_type: str | None = None
    list_date: str | None = None
    sale_total: str | None = None
    sale_date: str | None = None
    shipping: str | None = None
    sale_fee: str | None = None
    usd_to_jpy_rate: str | None = None
    group_discount: bool = False
    object_variant: str | None = None
    audit_target: bool = False
    cracked_from_purchase: bool = False
    qualifiers: list[str] = field(default_factory=list)

    @classmethod
    def as_form(
        cls,
        qualifiers: Annotated[list[str], Form(default_factory=list)],
        name: Annotated[str | None, Form()] = None,
        set_name: Annotated[str | None, Form()] = None,
        category: Annotated[str | None, Form()] = None,
        language: Annotated[str | None, Form()] = None,
        details: Annotated[str | None, Form()] = None,
        purchase_date: Annotated[str | None, Form()] = None,
        purchase_price: Annotated[str | None, Form()] = None,
        status: Annotated[str | None, Form()] = None,
        intent: Annotated[str | None, Form()] = None,
        import_fee: Annotated[str | None, Form()] = None,
        purchase_grading_company: Annotated[str | None, Form()] = None,
        purchase_grade: Annotated[str | None, Form()] = None,
        purchase_cert: Annotated[str | None, Form()] = None,
        list_price: Annotated[str | None, Form()] = None,
        list_type: Annotated[str | None, Form()] = None,
        list_date: Annotated[str | None, Form()] = None,
        sale_total: Annotated[str | None, Form()] = None,
        sale_date: Annotated[str | None, Form()] = None,
        shipping: Annotated[str | None, Form()] = None,
        sale_fee: Annotated[str | None, Form()] = None,
        usd_to_jpy_rate: Annotated[str | None, Form()] = None,
        object_variant: Annotated[str | None, Form()] = None,
        group_discount: Annotated[bool, Form()] = False,
        audit_target: Annotated[bool, Form()] = False,
        cracked_from_purchase: Annotated[bool, Form()] = False,
    ) -> 'ItemUpdateForm':
        return cls(
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

    def to_item_update(self) -> ItemUpdate:
        update_vals: dict[str, Any] = {}
        set_if_value(update_vals, 'name', parse_nullable(self.name, str))
        set_if_value(update_vals, 'set_name', parse_nullable(self.set_name, str))
        set_if_value(update_vals, 'category', parse_nullable_enum(self.category, Category))
        set_if_value(update_vals, 'language', parse_nullable_enum(self.language, Language))
        set_if_value(update_vals, 'qualifiers', parse_to_qualifiers_list(self.qualifiers))
        set_if_value(update_vals, 'details', parse_nullable(self.details, str))
        set_if_value(update_vals, 'purchase_date', parse_nullable_date(self.purchase_date))
        set_if_value(update_vals, 'purchase_price', parse_nullable(self.purchase_price, int))
        set_if_value(update_vals, 'status', parse_nullable_enum(self.status, Status))
        set_if_value(update_vals, 'intent', parse_nullable_enum(self.intent, Intent))
        set_if_value(update_vals, 'import_fee', parse_nullable(self.import_fee, int))
        set_if_value(
            update_vals,
            'purchase_grading_company',
            parse_nullable_enum(self.purchase_grading_company, GradingCompany),
        )
        set_if_value(update_vals, 'purchase_grade', parse_nullable(self.purchase_grade, float))
        set_if_value(update_vals, 'purchase_cert', parse_nullable(self.purchase_cert, int))
        set_if_value(update_vals, 'list_price', parse_nullable(self.list_price, float))
        set_if_value(update_vals, 'list_type', parse_nullable_enum(self.list_type, ListingType))
        set_if_value(update_vals, 'list_date', parse_nullable_date(self.list_date))
        set_if_value(update_vals, 'sale_total', parse_nullable(self.sale_total, float))
        set_if_value(update_vals, 'sale_date', parse_nullable_date(self.sale_date))
        set_if_value(update_vals, 'shipping', parse_nullable(self.shipping, float))
        set_if_value(update_vals, 'sale_fee', parse_nullable(self.sale_fee, float))
        set_if_value(update_vals, 'usd_to_jpy_rate', parse_nullable(self.usd_to_jpy_rate, float))
        set_if_value(update_vals, 'group_discount', self.group_discount)
        set_if_value(
            update_vals,
            'object_variant',
            parse_nullable_enum(self.object_variant, ObjectVariant),
        )
        set_if_value(update_vals, 'audit_target', self.audit_target)
        set_if_value(update_vals, 'cracked_from_purchase', self.cracked_from_purchase)
        return ItemUpdate(**update_vals)


class ItemSearch(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str | None, Form()] = None
    set_name: Annotated[str | None, Form()] = None
    category: Annotated[Category | None, Form()] = None
    language: Annotated[Language | None, Form()] = None
    qualifiers: Annotated[list[Qualifier], Form()] = []
    details: Annotated[str | None, Form()] = None
    purchase_date_min: Annotated[date | None, Form()] = None
    purchase_date_max: Annotated[date | None, Form()] = None
    purchase_price_min: Annotated[int | None, Form()] = None
    purchase_price_max: Annotated[int | None, Form()] = None
    status: Annotated[Status | None, Form()] = None
    intent: Annotated[Intent | None, Form()] = None
    cracked_from: Annotated[int | None, Form()] = None
    grading_company: Annotated[GradingCompany | None, Form()] = None
    grade: Annotated[float | None, Form()] = None
    cert: Annotated[int | None, Form()] = None
    list_type: Annotated[ListingType | None, Form()] = None
    list_date_min: Annotated[date | None, Form()] = None
    list_date_max: Annotated[date | None, Form()] = None
    sale_total_min: Annotated[float | None, Form()] = None
    sale_total_max: Annotated[float | None, Form()] = None
    sale_date_min: Annotated[date | None, Form()] = None
    sale_date_max: Annotated[date | None, Form()] = None
    group_discount: Annotated[bool | None, Form()] = None
    object_variant: Annotated[ObjectVariant | None, Form()] = None
    audit_target: Annotated[bool | None, Form()] = None
    total_cost_min: Annotated[int | None, Form()] = None
    total_cost_max: Annotated[int | None, Form()] = None
    return_jpy_min: Annotated[int | None, Form()] = None
    return_jpy_max: Annotated[int | None, Form()] = None
    net_jpy_min: Annotated[int | None, Form()] = None
    net_jpy_max: Annotated[int | None, Form()] = None
    net_percent_min: Annotated[float | None, Form()] = None
    net_percent_max: Annotated[float | None, Form()] = None


@dataclass
class ItemSearchForm:
    name: str | None = None
    set_name: str | None = None
    category: str | None = None
    language: str | None = None
    qualifiers: list[str] | None = None
    details: str | None = None
    purchase_date_min: str | None = None
    purchase_date_max: str | None = None
    purchase_price_min: str | None = None
    purchase_price_max: str | None = None
    status: str | None = None
    intent: str | None = None
    cracked_from: str | None = None
    grading_company: str | None = None
    grade: str | None = None
    cert: str | None = None
    list_type: str | None = None
    list_date_min: str | None = None
    list_date_max: str | None = None
    sale_total_min: str | None = None
    sale_total_max: str | None = None
    sale_date_min: str | None = None
    sale_date_max: str | None = None
    group_discount: str | None = None
    object_variant: str | None = None
    audit_target: str | None = None
    total_cost_min: str | None = None
    total_cost_max: str | None = None
    return_jpy_min: str | None = None
    return_jpy_max: str | None = None
    net_jpy_min: str | None = None
    net_jpy_max: str | None = None
    net_percent_min: str | None = None
    net_percent_max: str | None = None

    @classmethod
    def as_query(
        cls,
        name: Annotated[str | None, Query()] = None,
        set_name: Annotated[str | None, Query()] = None,
        category: Annotated[str | None, Query()] = None,
        language: Annotated[str | None, Query()] = None,
        qualifiers: Annotated[list[str], Query()] = [],
        details: Annotated[str | None, Query()] = None,
        purchase_date_min: Annotated[str | None, Query()] = None,
        purchase_date_max: Annotated[str | None, Query()] = None,
        purchase_price_min: Annotated[str | None, Query()] = None,
        purchase_price_max: Annotated[str | None, Query()] = None,
        status: Annotated[str | None, Query()] = None,
        intent: Annotated[str | None, Query()] = None,
        cracked_from: Annotated[str | None, Query()] = None,
        grading_company: Annotated[str | None, Query()] = None,
        grade: Annotated[str | None, Query()] = None,
        cert: Annotated[str | None, Query()] = None,
        list_type: Annotated[str | None, Query()] = None,
        list_date_min: Annotated[str | None, Query()] = None,
        list_date_max: Annotated[str | None, Query()] = None,
        sale_total_min: Annotated[str | None, Query()] = None,
        sale_total_max: Annotated[str | None, Query()] = None,
        sale_date_min: Annotated[str | None, Query()] = None,
        sale_date_max: Annotated[str | None, Query()] = None,
        object_variant: Annotated[str | None, Query()] = None,
        total_cost_min: Annotated[str | None, Query()] = None,
        total_cost_max: Annotated[str | None, Query()] = None,
        return_jpy_min: Annotated[str | None, Query()] = None,
        return_jpy_max: Annotated[str | None, Query()] = None,
        net_jpy_min: Annotated[str | None, Query()] = None,
        net_jpy_max: Annotated[str | None, Query()] = None,
        net_percent_min: Annotated[str | None, Query()] = None,
        net_percent_max: Annotated[str | None, Query()] = None,
        group_discount: Annotated[str | None, Query()] = None,
        audit_target: Annotated[str | None, Query()] = None,
    ) -> 'ItemSearchForm':
        return cls(
            name=name,
            set_name=set_name,
            category=category,
            language=language,
            qualifiers=qualifiers,
            details=details,
            purchase_date_min=purchase_date_min,
            purchase_date_max=purchase_date_max,
            purchase_price_min=purchase_price_min,
            purchase_price_max=purchase_price_max,
            status=status,
            intent=intent,
            cracked_from=cracked_from,
            grading_company=grading_company,
            grade=grade,
            cert=cert,
            list_type=list_type,
            list_date_min=list_date_min,
            list_date_max=list_date_max,
            sale_total_min=sale_total_min,
            sale_total_max=sale_total_max,
            sale_date_min=sale_date_min,
            sale_date_max=sale_date_max,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
            total_cost_min=total_cost_min,
            total_cost_max=total_cost_max,
            return_jpy_min=return_jpy_min,
            return_jpy_max=return_jpy_max,
            net_jpy_min=net_jpy_min,
            net_jpy_max=net_jpy_max,
            net_percent_min=net_percent_min,
            net_percent_max=net_percent_max,
        )

    def to_item_search(self) -> ItemSearch:
        return ItemSearch(
            name=parse_nullable(self.name, str),
            set_name=parse_nullable(self.set_name, str),
            category=parse_nullable_enum(self.category, Category),
            language=parse_nullable_enum(self.language, Language),
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date_min=parse_nullable_date(self.purchase_date_min),
            purchase_date_max=parse_nullable_date(self.purchase_date_max),
            purchase_price_min=parse_nullable(self.purchase_price_min, int),
            purchase_price_max=parse_nullable(self.purchase_price_max, int),
            status=parse_nullable_enum(self.status, Status),
            intent=parse_nullable_enum(self.intent, Intent),
            cracked_from=parse_nullable(self.cracked_from, int),
            grading_company=parse_nullable_enum(self.grading_company, GradingCompany),
            grade=parse_nullable(self.grade, float),
            cert=parse_nullable(self.cert, int),
            list_type=parse_nullable_enum(self.list_type, ListingType),
            list_date_min=parse_nullable_date(self.list_date_min),
            list_date_max=parse_nullable_date(self.list_date_max),
            sale_total_min=parse_nullable(self.sale_total_min, float),
            sale_total_max=parse_nullable(self.sale_total_max, float),
            sale_date_min=parse_nullable_date(self.sale_date_min),
            sale_date_max=parse_nullable_date(self.sale_date_max),
            group_discount=parse_nullable_bool(self.group_discount),
            object_variant=parse_nullable_enum(self.object_variant, ObjectVariant),
            audit_target=parse_nullable_bool(self.audit_target),
            total_cost_min=parse_nullable(self.total_cost_min, int),
            total_cost_max=parse_nullable(self.total_cost_max, int),
            return_jpy_min=parse_nullable(self.return_jpy_min, int),
            return_jpy_max=parse_nullable(self.return_jpy_max, int),
            net_jpy_min=parse_nullable(self.net_jpy_min, int),
            net_jpy_max=parse_nullable(self.net_jpy_max, int),
            net_percent_min=parse_nullable_percent(self.net_percent_min),
            net_percent_max=parse_nullable_percent(self.net_percent_max),
        )


class ItemForSubmissionForm(BaseModel):
    '''
    This is necessary for usage with javascript to provide nicely formatted strings that can be
    used as is in the display. If further information about an item is required it can be added
    here.
    '''
    model_config = ConfigDict(
        extra='forbid',
        from_attributes=True,
    )

    name: str
    set_name: str
    category: str
    language: str
    intent: str
    purchase_date: date
    purchase_price: int
    status: str
    qualifiers: list[str]
    details: str | None


class SubmissionBase(BaseModel):
    model_config = ConfigDict(extra='forbid')

    submission_number: int | None = None
    submission_company: GradingCompany | None = None
    submission_date: date | None = None
    return_date: date | None = None
    break_even_date: date | None = None


class SubmissionCreate(SubmissionBase):
    submission_number: int
    submission_company: GradingCompany

    def to_model_kwargs(self) -> dict[str, int | date | None]:
        return self.model_dump()


class SubmissionUpdate(SubmissionBase):
    def to_model_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


@dataclass
class SubmissionUpdateForm:
    submission_number: str | None = None
    submission_company: str | None = None
    submission_date: str | None = None
    return_date: str | None = None
    break_even_date: str | None = None

    @classmethod
    def as_form(
        cls,
        submission_number: Annotated[str | None, Form()] = None,
        submission_company: Annotated[str | None, Form()] = None,
        submission_date: Annotated[str | None, Form()] = None,
        return_date: Annotated[str | None, Form()] = None,
        break_even_date: Annotated[str | None, Form()] = None,
    ) -> 'SubmissionUpdateForm':
        return cls(
            submission_number=submission_number,
            submission_company=submission_company,
            submission_date=submission_date,
            return_date=return_date,
            break_even_date=break_even_date,
        )

    def to_submission_update(self) -> SubmissionUpdate:
        update_vals: dict[str, Any] = {}
        set_if_value(update_vals, 'submission_number', parse_nullable(self.submission_number, int))
        set_if_value(
            update_vals,
            'submission_company',
            parse_nullable_enum(self.submission_company, GradingCompany),
        )
        set_if_value(update_vals, 'submission_date', parse_nullable_date(self.submission_date))
        set_if_value(update_vals, 'return_date', parse_nullable_date(self.return_date))
        set_if_value(update_vals, 'break_even_date', parse_nullable_date(self.break_even_date))
        return SubmissionUpdate(**update_vals)


class GradingRecordBase(BaseModel):
    model_config = ConfigDict(extra='forbid')

    item_id: int | None = None
    submission_id: int | None = None
    grading_fee: int | None = None
    grade: float | None = None
    cert: int | None = None
    is_cracked: bool = False


class GradingRecordCreate(GradingRecordBase):
    item_id: int
    submission_id: int

    def to_model_kwargs(self) -> dict[str, int | float | bool | None]:
        return self.model_dump()


class GradingRecordUpdate(GradingRecordBase):
    def to_model_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


@dataclass
class GradingRecordUpdateForm:
    item_id: str | None = None
    submission_id: str | None = None
    grading_fee: str | None = None
    grade: str | None = None
    cert: str | None = None
    is_cracked: bool = False

    @classmethod
    def as_form(
        cls,
        item_id: Annotated[str | None, Form()] = None,
        submission_id: Annotated[str | None, Form()] = None,
        grading_fee: Annotated[str | None, Form()] = None,
        grade: Annotated[str | None, Form()] = None,
        cert: Annotated[str | None, Form()] = None,
        is_cracked: Annotated[bool, Form()] = False,
    ) -> 'GradingRecordUpdateForm':
        return cls(
            item_id=item_id,
            submission_id=submission_id,
            grading_fee=grading_fee,
            grade=grade,
            cert=cert,
            is_cracked=is_cracked,
        )

    def to_grading_record_update(self) -> GradingRecordUpdate:
        update_vals: dict[str, Any] = {}
        set_if_value(update_vals, 'item_id', parse_nullable(self.item_id, int))
        set_if_value(update_vals, 'submission_id', parse_nullable(self.submission_id, int))
        set_if_value(update_vals, 'grading_fee', parse_nullable(self.grading_fee, int))
        set_if_value(update_vals, 'grade', parse_nullable(self.grade, float))
        set_if_value(update_vals, 'cert', parse_nullable(self.cert, int))
        set_if_value(update_vals, 'is_cracked', self.is_cracked)
        return GradingRecordUpdate(**update_vals)


def set_if_value(
    d: dict[str, Any],
    key: str,
    value: Any,
) -> None:
    if value is not None and value != '' and value != [] and value != {}:
        d[key] = value
