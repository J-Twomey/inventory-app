import json
from dataclasses import (
    dataclass,
    field,
)

from datetime import (
    date,
    datetime,
)
from enum import Enum
from typing import (
    Annotated,
    Any,
    Type,
    TypeVar,
)

from fastapi import Form
from pydantic import (
    BaseModel,
    computed_field,
    ConfigDict,
    field_validator,
    ValidationInfo,
)

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


T = TypeVar('T', bound=Enum)


class ItemBase(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str, Form()]
    set_name: Annotated[str, Form()]
    category: Annotated[Category, Form()]
    language: Annotated[Language, Form()]
    qualifiers: Annotated[list[Qualifier], Form(default_factory=list)]
    details: Annotated[str | None, Form()] = None
    purchase_date: Annotated[date, Form()]
    purchase_price: Annotated[int, Form()]
    status: Annotated[Status, Form()]
    intent: Annotated[Intent, Form()]
    grading_fee: Annotated[dict[int, int], Form(default_factory=dict)]
    grade: Annotated[float | None, Form()] = None
    grading_company: Annotated[GradingCompany, Form()]
    cert: Annotated[int | None, Form()] = None
    submission_number: Annotated[list[int], Form(default_factory=list)]
    list_price: Annotated[float | None, Form()] = None
    list_type: Annotated[ListingType, Form()]
    list_date: Annotated[date | None, Form()] = None
    sale_total: Annotated[float | None, Form()] = None
    sale_date: Annotated[date | None, Form()] = None
    shipping: Annotated[float | None, Form()] = None
    sale_fee: Annotated[float | None, Form()] = None
    usd_to_jpy_rate: Annotated[float | None, Form()] = None
    group_discount: Annotated[bool, Form()] = False
    object_variant: Annotated[ObjectVariant, Form()]
    audit_target: Annotated[bool, Form()] = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def grading_fee_total(self) -> int:
        return sum(self.grading_fee.values())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_cost(self) -> int:
        return self.purchase_price + self.grading_fee_total

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_fees(self) -> float | None:
        if self.shipping is None or self.sale_fee is None:
            return None
        else:
            return self.shipping + self.sale_fee

    @computed_field  # type: ignore[prop-decorator]
    @property
    def return_usd(self) -> float | None:
        if self.sale_total is None or self.total_fees is None:
            return None
        else:
            return self.sale_total - self.total_fees

    @computed_field  # type: ignore[prop-decorator]
    @property
    def return_jpy(self) -> int | None:
        if self.return_usd is None or self.usd_to_jpy_rate is None:
            return None
        else:
            return round(self.return_usd * self.usd_to_jpy_rate)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def net_jpy(self) -> int | None:
        if self.return_jpy is None:
            return None
        else:
            return round(self.return_jpy - self.total_cost)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def net_percent(self) -> float | None:
        if self.net_jpy is None:
            return None
        elif self.total_cost == 0:
            return 0.
        else:
            return round(100 * self.net_jpy / self.total_cost, 2)

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(
            cls,
            v: T,
            info: ValidationInfo,
    ) -> T | None:
        if info.field_name in {
            'qualifiers',
            'grading_fee',
            'submission_number',
            'group_discount',
            'audit_target',
        }:
            return v
        if v == '':
            return None
        return v

    @field_validator('submission_number', mode='before')
    @classmethod
    def parse_submission_numbers(cls, v: Any) -> list[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',') if x.strip()]
        elif isinstance(v, list) and all(isinstance(x, int) for x in v):
            return v
        raise ValueError('submission_number must be provided as str or list[int]')

    @field_validator('qualifiers', mode='before')
    @classmethod
    def parse_qualifiers(cls, v: Any) -> list[Qualifier]:
        if isinstance(v, str):
            return [Qualifier[x.strip()] for x in v.split(',') if x.strip()]
        elif isinstance(v, list) and all(isinstance(x, Qualifier) for x in v):
            return v
        raise ValueError('qualifiers must be provided as str or list[Qualifier]')

    @field_validator('grading_fee', mode='before')
    @classmethod
    def parse_grading_fee(cls, v: Any) -> dict[int, int]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return {int(k): int(v) for k, v in parsed.items()}
            except Exception:
                raise ValueError('grading_fee must be valid JSON')
        elif (
            isinstance(v, dict)
            and all(isinstance(x, int) for x in v)
            and all(isinstance(z, int) for z in v.values())
        ):
            return v
        raise ValueError('grading_fee must be provided as str or dict[int, int]')


class ItemCreate(ItemBase):
    pass


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
    grading_fee: str
    grade: str
    grading_company: str
    cert: str
    submission_number: str
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
        grading_fee: Annotated[str, Form()],
        grade: Annotated[str, Form()],
        grading_company: Annotated[str, Form()],
        cert: Annotated[str, Form()],
        submission_number: Annotated[str, Form()],
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
            grading_fee=grading_fee,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
            submission_number=submission_number,
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
            category=parse_enum(self.category, Category, 'category'),
            language=parse_enum(self.language, Language, 'language'),
            qualifiers=parse_to_qualifiers_list_new(self.qualifiers),
            details=parse_nullable_string(self.details),
            purchase_date=purchase_date_,
            purchase_price=int(self.purchase_price),
            status=parse_enum(self.status, Status, 'status'),
            intent=parse_enum(self.intent, Intent, 'intent'),
            grading_fee=parse_to_dict(self.grading_fee or '{}'),
            grade=parse_nullable_float(self.grade),
            grading_company=parse_enum(self.grading_company, GradingCompany, 'grading_company'),
            cert=parse_nullable_int(self.cert),
            submission_number=parse_to_int_list(self.submission_number),
            list_price=parse_nullable_float(self.list_price),
            list_type=parse_enum(self.list_type, ListingType, 'list_type'),
            list_date=list_date_,
            sale_total=parse_nullable_float(self.sale_total),
            sale_date=sale_date_,
            shipping=parse_nullable_float(self.shipping),
            sale_fee=parse_nullable_float(self.sale_fee),
            usd_to_jpy_rate=parse_nullable_float(self.usd_to_jpy_rate),
            group_discount=self.group_discount,
            object_variant=parse_enum(self.object_variant, ObjectVariant, 'object_variant'),
            audit_target=self.audit_target,
        )


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str | None, Form(None)] = None
    set_name: Annotated[str | None, Form(None)] = None
    category: Annotated[Category | None, Form(None)] = None
    language: Annotated[Language | None, Form(None)] = None
    qualifiers: Annotated[list[Qualifier] | None, Form(None)] = None
    details: Annotated[str | None, Form(None)] = None
    purchase_date: Annotated[date | None, Form(None)] = None
    purchase_price: Annotated[int | None, Form(None)] = None
    status: Annotated[Status | None, Form(None)] = None
    intent: Annotated[Intent | None, Form(None)] = None
    grading_fee: Annotated[dict[int, int] | None, Form(None)] = None
    grade: Annotated[float | None, Form(None)] = None
    grading_company: Annotated[GradingCompany | None, Form(None)] = None
    cert: Annotated[int | None, Form(None)] = None
    submission_number: Annotated[list[int] | None, Form(None)] = None
    list_price: Annotated[float | None, Form(None)] = None
    list_type: Annotated[ListingType | None, Form(None)] = None
    list_date: Annotated[date | None, Form(None)] = None
    sale_total: Annotated[float | None, Form(None)] = None
    sale_date: Annotated[date | None, Form(None)] = None
    shipping: Annotated[float | None, Form(None)] = None
    sale_fee: Annotated[float | None, Form(None)] = None
    usd_to_jpy: Annotated[float | None, Form(None)] = None
    group_discount: Annotated[bool | None, Form(None)] = None
    object_variant: Annotated[ObjectVariant | None, Form(None)] = None
    audit_target: Annotated[bool | None, Form(None)] = None


@dataclass
class ItemUpdateForm:
    name: str | None = None
    set_name: str | None = None
    category: str | None = None
    language: str | None = None
    qualifiers: str | None = None
    details: str | None = None
    purchase_date: str | None = None
    purchase_price: str | None = None
    status: str | None = None
    intent: str | None = None
    grading_fee: str | None = None
    grade: str | None = None
    grading_company: str | None = None
    cert: str | None = None
    submission_number: str | None = None
    list_price: str | None = None
    list_type: str | None = None
    list_date: str | None = None
    sale_total: str | None = None
    sale_date: str | None = None
    shipping: str | None = None
    sale_fee: str | None = None
    usd_to_jpy: str | None = None
    group_discount: str | bool | None = None
    object_variant: str | None = None
    audit_target: str | bool | None = None

    @classmethod
    def as_form(
        cls,
        name: Annotated[str | None, Form()] = None,
        set_name: Annotated[str | None, Form()] = None,
        category: Annotated[str | None, Form()] = None,
        language: Annotated[str | None, Form()] = None,
        qualifiers: Annotated[str | None, Form()] = None,
        details: Annotated[str | None, Form()] = None,
        purchase_date: Annotated[str | None, Form()] = None,
        purchase_price: Annotated[str | None, Form()] = None,
        status: Annotated[str | None, Form()] = None,
        intent: Annotated[str | None, Form()] = None,
        grading_fee: Annotated[str | None, Form()] = None,
        grade: Annotated[str | None, Form()] = None,
        grading_company: Annotated[str | None, Form()] = None,
        cert: Annotated[str | None, Form()] = None,
        submission_number: Annotated[str | None, Form()] = None,
        list_price: Annotated[str | None, Form()] = None,
        list_type: Annotated[str | None, Form()] = None,
        list_date: Annotated[str | None, Form()] = None,
        sale_total: Annotated[str | None, Form()] = None,
        sale_date: Annotated[str | None, Form()] = None,
        shipping: Annotated[str | None, Form()] = None,
        sale_fee: Annotated[str | None, Form()] = None,
        usd_to_jpy: Annotated[str | None, Form()] = None,
        object_variant: Annotated[str | None, Form()] = None,
        group_discount: Annotated[bool | None, Form()] = None,
        audit_target: Annotated[bool | None, Form()] = None,
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
            grading_fee=grading_fee,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
            submission_number=submission_number,
            list_price=list_price,
            list_type=list_type,
            list_date=list_date,
            sale_total=sale_total,
            sale_date=sale_date,
            shipping=shipping,
            sale_fee=sale_fee,
            usd_to_jpy=usd_to_jpy,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
        )

    def to_item_update(self) -> ItemUpdate:
        update_vals: dict[str, Any] = {}
        set_if_value(update_vals, 'name', parse_nullable_string(self.name))
        set_if_value(update_vals, 'set_name', parse_nullable_string(self.set_name))
        set_if_value(
            update_vals,
            'category',
            parse_nullable_enum(self.category, Category, 'category'),
        )
        set_if_value(
            update_vals,
            'language',
            parse_nullable_enum(self.language, Language, 'language'),
        )
        set_if_value(update_vals, 'qualifiers', parse_to_qualifiers_list(self.qualifiers))
        set_if_value(update_vals, 'details', parse_nullable_string(self.details))
        set_if_value(update_vals, 'purchase_date', parse_nullable_date(self.purchase_date))
        set_if_value(update_vals, 'purchase_price', parse_nullable_int(self.purchase_price))
        set_if_value(update_vals, 'status', parse_nullable_enum(self.status, Status, 'status'))
        set_if_value(update_vals, 'intent', parse_nullable_enum(self.intent, Intent, 'intent'))
        set_if_value(update_vals, 'grading_fee', parse_to_nullable_dict(self.grading_fee))
        set_if_value(update_vals, 'grade', parse_nullable_float(self.grade))
        set_if_value(
            update_vals,
            'grading_company',
            parse_nullable_enum(self.grading_company, GradingCompany, 'grading_company'),
        )
        set_if_value(update_vals, 'cert', parse_nullable_int(self.cert))
        set_if_value(update_vals, 'submission_number', parse_to_int_list(self.submission_number))
        set_if_value(update_vals, 'list_price', parse_nullable_float(self.list_price))
        set_if_value(
            update_vals,
            'list_type',
            parse_nullable_enum(self.list_type, ListingType, 'list_type'),
        )
        set_if_value(update_vals, 'list_date', parse_nullable_date(self.list_date))
        set_if_value(update_vals, 'sale_total', parse_nullable_float(self.sale_total))
        set_if_value(update_vals, 'sale_date', parse_nullable_date(self.sale_date))
        set_if_value(update_vals, 'shipping', parse_nullable_float(self.shipping))
        set_if_value(update_vals, 'sale_fee', parse_nullable_float(self.sale_fee))
        set_if_value(update_vals, 'usd_to_jpy', parse_nullable_float(self.usd_to_jpy))
        set_if_value(update_vals, 'group_discount', parse_nullable_bool(self.group_discount))
        set_if_value(
            update_vals,
            'object_variant',
            parse_nullable_enum(self.object_variant, ObjectVariant, 'object_variant'),
        )
        set_if_value(update_vals, 'audit_target', parse_nullable_bool(self.audit_target))
        return ItemUpdate(**update_vals)


class ItemSearch(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str | None, Form(None)] = None
    set_name: Annotated[str | None, Form(None)] = None
    category: Annotated[Category | None, Form(None)] = None
    language: Annotated[Language | None, Form(None)] = None
    qualifiers: Annotated[list[Qualifier], Form(default_factory=list)]
    details: Annotated[str | None, Form(None)] = None
    purchase_date: Annotated[date | None, Form(None)] = None
    purchase_price: Annotated[int | None, Form(None)] = None
    status: Annotated[Status | None, Form(None)] = None
    intent: Annotated[Intent | None, Form(None)] = None
    grade: Annotated[float | None, Form(None)] = None
    grading_company: Annotated[GradingCompany | None, Form(None)] = None
    cert: Annotated[int | None, Form(None)] = None
    submission_number: Annotated[list[int], Form(default_factory=list)]
    list_type: Annotated[ListingType | None, Form(None)] = None
    list_date: Annotated[date | None, Form(None)] = None
    sale_total: Annotated[float | None, Form(None)] = None
    sale_date: Annotated[date | None, Form(None)] = None
    group_discount: Annotated[bool | None, Form(None)] = None
    object_variant: Annotated[ObjectVariant | None, Form(None)] = None
    audit_target: Annotated[bool | None, Form(None)] = None
    total_cost: Annotated[int | None, Form(None)] = None
    return_jpy: Annotated[int | None, Form(None)] = None
    net_jpy: Annotated[int | None, Form(None)] = None
    net_percent: Annotated[float | None, Form(None)] = None


@dataclass
class ItemSearchForm:
    name: str | None = None
    set_name: str | None = None
    category: str | None = None
    language: str | None = None
    qualifiers: list[str] | None = None
    details: str | None = None
    purchase_date: str | None = None
    purchase_price: str | None = None
    status: str | None = None
    intent: str | None = None
    grade: str | None = None
    grading_company: str | None = None
    cert: str | None = None
    submission_number: str | None = None
    list_type: str | None = None
    list_date: str | None = None
    sale_total: str | None = None
    sale_date: str | None = None
    group_discount: str | bool | None = None
    object_variant: str | None = None
    audit_target: str | bool | None = None
    total_cost: str | None = None
    return_jpy: str | None = None
    net_jpy: str | None = None
    net_percent: str | None = None

    @classmethod
    def as_form(
        cls,
        name: Annotated[str, Form()],
        set_name: Annotated[str, Form()],
        category: Annotated[str, Form()],
        language: Annotated[str, Form()],
        qualifiers: Annotated[list[str], Form()],
        details: Annotated[str, Form()],
        purchase_date: Annotated[str, Form()],
        purchase_price: Annotated[str, Form()],
        status: Annotated[str, Form()],
        intent: Annotated[str, Form()],
        grade: Annotated[str, Form()],
        grading_company: Annotated[str, Form()],
        cert: Annotated[str, Form()],
        submission_number: Annotated[str, Form()],
        list_type: Annotated[str, Form()],
        list_date: Annotated[str, Form()],
        sale_total: Annotated[str, Form()],
        sale_date: Annotated[str, Form()],
        object_variant: Annotated[str, Form()],
        total_cost: Annotated[str, Form()],
        return_jpy: Annotated[str, Form()],
        net_jpy: Annotated[str, Form()],
        net_percent: Annotated[str, Form()],
        group_discount: Annotated[bool, Form()] = False,
        audit_target: Annotated[bool, Form()] = False,
    ) -> 'ItemSearchForm':
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
            grade=grade,
            grading_company=grading_company,
            cert=cert,
            submission_number=submission_number,
            list_type=list_type,
            list_date=list_date,
            sale_total=sale_total,
            sale_date=sale_date,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
            total_cost=total_cost,
            return_jpy=return_jpy,
            net_jpy=net_jpy,
            net_percent=net_percent,
        )

    def to_item_search(self) -> ItemSearch:
        if self.purchase_date == '' or self.purchase_date is None:
            purchase_date_ = None
        else:
            purchase_date_ = datetime.strptime(self.purchase_date, '%Y-%m-%d').date()
        if self.list_date == '' or self.list_date is None:
            list_date_ = None
        else:
            list_date_ = datetime.strptime(self.list_date, '%Y-%m-%d').date()
        if self.sale_date == '' or self.sale_date is None:
            sale_date_ = None
        else:
            sale_date_ = datetime.strptime(self.sale_date, '%Y-%m-%d').date()
        return ItemSearch(
            name=parse_nullable_string(self.name),
            set_name=parse_nullable_string(self.set_name),
            category=parse_nullable_enum(self.category, Category, 'category'),
            language=parse_nullable_enum(self.language, Language, 'language'),
            qualifiers=parse_to_qualifiers_list_new(self.qualifiers),
            details=parse_nullable_string(self.details),
            purchase_date=purchase_date_,
            purchase_price=parse_nullable_int(self.purchase_price),
            status=parse_nullable_enum(self.status, Status, 'status'),
            intent=parse_nullable_enum(self.intent, Intent, 'intent'),
            grade=parse_nullable_float(self.grade),
            grading_company=parse_nullable_enum(
                self.grading_company,
                GradingCompany,
                'grading_company',
            ),
            cert=parse_nullable_int(self.cert),
            submission_number=parse_to_int_list(self.submission_number),
            list_type=parse_nullable_enum(self.list_type, ListingType, 'list_type'),
            list_date=list_date_,
            sale_total=parse_nullable_float(self.sale_total),
            sale_date=sale_date_,
            group_discount=parse_nullable_bool(self.group_discount),
            object_variant=parse_nullable_enum(
                self.object_variant,
                ObjectVariant,
                'object_variant',
            ),
            audit_target=parse_nullable_bool(self.audit_target),
            total_cost=parse_nullable_int(self.total_cost),
            return_jpy=parse_nullable_int(self.return_jpy),
            net_jpy=parse_nullable_int(self.net_jpy),
            net_percent=parse_nullable_float(self.net_percent),
        )


def parse_enum(
        value: str,
        enum_cls: Type[T],
        enum_name: str,
) -> T:
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_name}: {value}')


def parse_nullable_enum(
        value: str | None,
        enum_cls: Type[T],
        enum_name: str,
) -> T | None:
    if value == '' or value is None:
        return None
    else:
        try:
            return enum_cls[value.upper()]
        except KeyError:
            raise ValueError(f'Invalid {enum_name}: {value}')


def parse_to_int_list(values: str | None) -> list[int]:
    if values is None:
        return []
    else:
        return [int(x.strip()) for x in values.split(',') if x.strip()]


def parse_to_qualifiers_list(values: str | None) -> list[Qualifier]:
    if values is None:
        return []
    else:
        return [Qualifier[x.strip()] for x in values.split(',') if x.strip()]


def parse_to_qualifiers_list_new(values: list[str] | None) -> list[Qualifier]:
    if values is None:
        return []
    else:
        return [Qualifier[x.upper()] for x in values]


def parse_to_dict(v: str) -> dict[int, int]:
    try:
        parsed: dict[str, str] = json.loads(v)
        return {int(k): int(v) for k, v in parsed.items()}
    except Exception:
        raise ValueError('grading_fee must be valid JSON')


def parse_to_nullable_dict(v: str | None) -> dict[int, int] | None:
    if v == '' or v is None:
        return None
    else:
        try:
            parsed: dict[str, str] = json.loads(v)
            return {int(k): int(v) for k, v in parsed.items()}
        except Exception:
            raise ValueError('grading_fee must be valid JSON')


def parse_nullable_string(v: str | None) -> str | None:
    if v == '' or v is None:
        return None
    else:
        return v


def parse_nullable_float(v: str | None) -> float | None:
    if v == '' or v is None:
        return None
    else:
        return float(v)


def parse_nullable_int(v: str | None) -> int | None:
    if v == '' or v is None:
        return None
    else:
        return int(v)


def parse_nullable_bool(v: str | bool | None) -> bool | None:
    if v == 'on':
        return True
    elif v == '':
        return None
    else:
        return False


def parse_nullable_date(date_str: str | None) -> date | None:
    if date_str is None or date_str == '':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def set_if_value(
        d: dict[str, Any],
        k: str,
        v: Any,
) -> None:
    if v is not None and v != '' and v != [] and v != {}:
        d[k] = v
