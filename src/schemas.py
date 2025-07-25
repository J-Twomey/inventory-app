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
    Callable,
    Literal,
    overload,
    Type,
    TypeVar,
)

from fastapi import (
    Form,
    Query,
)
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


E = TypeVar('E', bound=Enum)
T = TypeVar('T')


class ItemBase(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        from_attributes=True,
    )

    name: str
    set_name: str
    category: Category
    language: Language
    qualifiers: list[Qualifier]
    details: str | None = None
    purchase_date: date
    purchase_price: int
    status: Status
    intent: Intent
    grading_fee: dict[int, int]
    cracked_from: list[int]
    grade: float | None = None
    grading_company: GradingCompany
    cert: int | None = None
    list_price: float | None = None
    list_type: ListingType
    list_date: date | None = None
    sale_total: float | None = None
    sale_date: date | None = None
    shipping: float | None = None
    sale_fee: float | None = None
    usd_to_jpy_rate: float | None = None
    group_discount: bool = False
    object_variant: ObjectVariant
    audit_target: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def grading_fee_total(self) -> int:
        return sum(self.grading_fee.values())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def submission_numbers(self) -> list[int]:
        return list(self.grading_fee)

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
            return round(self.sale_total - self.total_fees, 2)

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
        # Empty string is handled differently for these fields
        if info.field_name in {
            'qualifiers',
            'grading_fee',
            'cracked_from',
            'group_discount',
            'audit_target',
        }:
            return v
        if v == '':
            return None
        return v

    @field_validator('qualifiers', mode='before')
    @classmethod
    def parse_qualifiers(cls, v: Any) -> list[Qualifier]:
        if isinstance(v, str):
            return [Qualifier[x.strip()] for x in v.split(',') if x.strip()]
        elif isinstance(v, list) and all(isinstance(x, Qualifier) for x in v):
            return v
        raise ValueError('qualifiers must be provided as str or list[Qualifier]')

    @field_validator('cracked_from', mode='before')
    @classmethod
    def parse_cracked_from(cls, v: Any) -> list[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',') if x.strip()]
        elif isinstance(v, list) and all(isinstance(x, int) for x in v):
            return v
        raise ValueError('cracked_from must be provided as str or list[int]')

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
    def to_model_kwargs(
            self,
            exclude: set[str] = set(),
    ) -> dict[str, Any]:
        data = self.model_dump(exclude=exclude)
        data['category'] = self.category.value
        data['language'] = self.language.value
        data['status'] = self.status.value
        data['intent'] = self.intent.value
        data['grading_company'] = self.grading_company.value
        data['list_type'] = self.list_type.value
        data['object_variant'] = self.object_variant.value
        return data


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
    grade: str
    grading_company: str
    cert: str
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
    submission_numbers: list[str] = field(default_factory=list)
    grading_fees: list[str] = field(default_factory=list)
    cracked_from: list[str] = field(default_factory=list)
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
        grade: Annotated[str, Form()],
        grading_company: Annotated[str, Form()],
        cert: Annotated[str, Form()],
        list_price: Annotated[str, Form()],
        list_type: Annotated[str, Form()],
        list_date: Annotated[str, Form()],
        sale_total: Annotated[str, Form()],
        sale_date: Annotated[str, Form()],
        shipping: Annotated[str, Form()],
        sale_fee: Annotated[str, Form()],
        usd_to_jpy_rate: Annotated[str, Form()],
        object_variant: Annotated[str, Form()],
        submission_numbers: Annotated[list[str], Form(default_factory=list)],
        grading_fees: Annotated[list[str], Form(default_factory=list)],
        cracked_from: Annotated[list[str], Form(default_factory=list)],
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
            submission_numbers=submission_numbers,
            grading_fees=grading_fees,
            cracked_from=cracked_from,
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
            category=parse_enum(self.category, Category),
            language=parse_enum(self.language, Language),
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date=purchase_date_,
            purchase_price=int(self.purchase_price),
            status=parse_enum(self.status, Status),
            intent=parse_enum(self.intent, Intent),
            grading_fee=build_grading_fee_dict(self.submission_numbers, self.grading_fees),
            cracked_from=parse_nullable_list_of_str_to_list_of_int(
                self.cracked_from,
            ),
            grade=parse_nullable(self.grade, float),
            grading_company=parse_enum(self.grading_company, GradingCompany),
            cert=parse_nullable(self.cert, int),
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
        )


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

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
    grading_fee: dict[int, int] | None = None
    cracked_from: list[int] | None = None
    grade: float | None = None
    grading_company: GradingCompany | None = None
    cert: int | None = None
    list_price: float | None = None
    list_type: ListingType | None = None
    list_date: date | None = None
    sale_total: float | None = None
    sale_date: date | None = None
    shipping: float | None = None
    sale_fee: float | None = None
    usd_to_jpy: float | None = None
    group_discount: bool = False
    object_variant: ObjectVariant | None = None
    audit_target: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def grading_fee_total(self) -> int | None:
        if self.grading_fee is not None:
            return sum(self.grading_fee.values())
        else:
            return None

    def to_model_kwargs(self) -> dict[str, Any]:
        data = self.model_dump(exclude_unset=True)
        if self.category is not None:
            data['category'] = self.category.value
        if self.language is not None:
            data['language'] = self.language.value
        if self.status is not None:
            data['status'] = self.status.value
        if self.intent is not None:
            data['intent'] = self.intent.value
        if self.grading_company is not None:
            data['grading_company'] = self.grading_company.value
        if self.list_type is not None:
            data['list_type'] = self.list_type.value
        if self.object_variant is not None:
            data['object_variant'] = self.object_variant.value
        if data.get('grading_fee_total') is None:
            data.pop('grading_fee_total', None)
        return data


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
    grading_fee: str | None = None
    grade: str | None = None
    grading_company: str | None = None
    cert: str | None = None
    list_price: str | None = None
    list_type: str | None = None
    list_date: str | None = None
    sale_total: str | None = None
    sale_date: str | None = None
    shipping: str | None = None
    sale_fee: str | None = None
    usd_to_jpy: str | None = None
    group_discount: bool = False
    object_variant: str | None = None
    audit_target: bool = False
    submission_numbers: list[str] = field(default_factory=list)
    grading_fees: list[str] = field(default_factory=list)
    cracked_from: list[str] = field(default_factory=list)
    qualifiers: list[str] = field(default_factory=list)

    @classmethod
    def as_form(
        cls,
        qualifiers: Annotated[list[str], Form(default_factory=list)],
        submission_numbers: Annotated[list[str], Form(default_factory=list)],
        grading_fees: Annotated[list[str], Form(default_factory=list)],
        cracked_from: Annotated[list[str], Form(default_factory=list)],
        name: Annotated[str | None, Form()] = None,
        set_name: Annotated[str | None, Form()] = None,
        category: Annotated[str | None, Form()] = None,
        language: Annotated[str | None, Form()] = None,
        details: Annotated[str | None, Form()] = None,
        purchase_date: Annotated[str | None, Form()] = None,
        purchase_price: Annotated[str | None, Form()] = None,
        status: Annotated[str | None, Form()] = None,
        intent: Annotated[str | None, Form()] = None,
        grade: Annotated[str | None, Form()] = None,
        grading_company: Annotated[str | None, Form()] = None,
        cert: Annotated[str | None, Form()] = None,
        list_price: Annotated[str | None, Form()] = None,
        list_type: Annotated[str | None, Form()] = None,
        list_date: Annotated[str | None, Form()] = None,
        sale_total: Annotated[str | None, Form()] = None,
        sale_date: Annotated[str | None, Form()] = None,
        shipping: Annotated[str | None, Form()] = None,
        sale_fee: Annotated[str | None, Form()] = None,
        usd_to_jpy: Annotated[str | None, Form()] = None,
        object_variant: Annotated[str | None, Form()] = None,
        group_discount: Annotated[bool, Form()] = False,
        audit_target: Annotated[bool, Form()] = False,
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
            usd_to_jpy=usd_to_jpy,
            submission_numbers=submission_numbers,
            grading_fees=grading_fees,
            cracked_from=cracked_from,
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
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
        set_if_value(update_vals, 'grade', parse_nullable(self.grade, float))
        set_if_value(
            update_vals,
            'grading_company',
            parse_nullable_enum(self.grading_company, GradingCompany),
        )
        set_if_value(update_vals, 'cert', parse_nullable(self.cert, int))
        set_if_value(update_vals, 'list_price', parse_nullable(self.list_price, float))
        set_if_value(update_vals, 'list_type', parse_nullable_enum(self.list_type, ListingType))
        set_if_value(update_vals, 'list_date', parse_nullable_date(self.list_date))
        set_if_value(update_vals, 'sale_total', parse_nullable(self.sale_total, float))
        set_if_value(update_vals, 'sale_date', parse_nullable_date(self.sale_date))
        set_if_value(update_vals, 'shipping', parse_nullable(self.shipping, float))
        set_if_value(update_vals, 'sale_fee', parse_nullable(self.sale_fee, float))
        set_if_value(update_vals, 'usd_to_jpy', parse_nullable(self.usd_to_jpy, float))
        set_if_value(
            update_vals,
            'cracked_from',
            parse_nullable_list_of_str_to_list_of_int(self.cracked_from),
        )
        set_if_value(update_vals, 'group_discount', self.group_discount)
        set_if_value(
            update_vals,
            'object_variant',
            parse_nullable_enum(self.object_variant, ObjectVariant),
        )
        set_if_value(update_vals, 'audit_target', self.audit_target)

        if len(self.submission_numbers) > 0 and len(self.grading_fees) > 0:
            update_vals['grading_fee'] = build_grading_fee_dict(
                self.submission_numbers,
                self.grading_fees,
            )
        return ItemUpdate(**update_vals)


class ItemSearch(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[str | None, Form()] = None
    set_name: Annotated[str | None, Form()] = None
    category: Annotated[int | None, Form()] = None
    language: Annotated[int | None, Form()] = None
    qualifiers: Annotated[list[Qualifier], Form()] = []
    details: Annotated[str | None, Form()] = None
    purchase_date: Annotated[date | None, Form()] = None
    purchase_price: Annotated[int | None, Form()] = None
    status: Annotated[int | None, Form()] = None
    intent: Annotated[int | None, Form()] = None
    cracked_from: Annotated[int | None, Form()] = None
    grade: Annotated[float | None, Form()] = None
    grading_company: Annotated[int | None, Form()] = None
    cert: Annotated[int | None, Form()] = None
    list_type: Annotated[int | None, Form()] = None
    list_date: Annotated[date | None, Form()] = None
    sale_total: Annotated[float | None, Form()] = None
    sale_date: Annotated[date | None, Form()] = None
    group_discount: Annotated[bool | None, Form()] = None
    object_variant: Annotated[int | None, Form()] = None
    audit_target: Annotated[bool | None, Form()] = None
    total_cost: Annotated[int | None, Form()] = None
    return_jpy: Annotated[int | None, Form()] = None
    net_jpy: Annotated[int | None, Form()] = None
    net_percent: Annotated[float | None, Form()] = None


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
    cracked_from: str | None = None
    grade: str | None = None
    grading_company: str | None = None
    cert: str | None = None
    list_type: str | None = None
    list_date: str | None = None
    sale_total: str | None = None
    sale_date: str | None = None
    group_discount: str | None = None
    object_variant: str | None = None
    audit_target: str | None = None
    total_cost: str | None = None
    return_jpy: str | None = None
    net_jpy: str | None = None
    net_percent: str | None = None

    @classmethod
    def as_query(
        cls,
        name: Annotated[str | None, Query()] = None,
        set_name: Annotated[str | None, Query()] = None,
        category: Annotated[str | None, Query()] = None,
        language: Annotated[str | None, Query()] = None,
        qualifiers: Annotated[list[str], Query()] = [],
        details: Annotated[str | None, Query()] = None,
        purchase_date: Annotated[str | None, Query()] = None,
        purchase_price: Annotated[str | None, Query()] = None,
        status: Annotated[str | None, Query()] = None,
        intent: Annotated[str | None, Query()] = None,
        cracked_from: Annotated[str | None, Query()] = None,
        grade: Annotated[str | None, Query()] = None,
        grading_company: Annotated[str | None, Query()] = None,
        cert: Annotated[str | None, Query()] = None,
        list_type: Annotated[str | None, Query()] = None,
        list_date: Annotated[str | None, Query()] = None,
        sale_total: Annotated[str | None, Query()] = None,
        sale_date: Annotated[str | None, Query()] = None,
        object_variant: Annotated[str | None, Query()] = None,
        total_cost: Annotated[str | None, Query()] = None,
        return_jpy: Annotated[str | None, Query()] = None,
        net_jpy: Annotated[str | None, Query()] = None,
        net_percent: Annotated[str | None, Query()] = None,
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
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            status=status,
            intent=intent,
            cracked_from=cracked_from,
            grade=grade,
            grading_company=grading_company,
            cert=cert,
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
            name=parse_nullable(self.name, str),
            set_name=parse_nullable(self.set_name, str),
            category=parse_nullable_enum(self.category, Category, as_int=True),
            language=parse_nullable_enum(self.language, Language, as_int=True),
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date=purchase_date_,
            purchase_price=parse_nullable(self.purchase_price, int),
            status=parse_nullable_enum(self.status, Status, as_int=True),
            intent=parse_nullable_enum(self.intent, Intent, as_int=True),
            cracked_from=parse_nullable(self.cracked_from, int),
            grade=parse_nullable(self.grade, float),
            grading_company=parse_nullable_enum(self.grading_company, GradingCompany, as_int=True),
            cert=parse_nullable(self.cert, int),
            list_type=parse_nullable_enum(self.list_type, ListingType, as_int=True),
            list_date=list_date_,
            sale_total=parse_nullable(self.sale_total, float),
            sale_date=sale_date_,
            group_discount=parse_nullable_bool(self.group_discount),
            object_variant=parse_nullable_enum(self.object_variant, ObjectVariant, as_int=True),
            audit_target=parse_nullable_bool(self.audit_target),
            total_cost=parse_nullable(self.total_cost, int),
            return_jpy=parse_nullable(self.return_jpy, int),
            net_jpy=parse_nullable(self.net_jpy, int),
            net_percent=parse_nullable(self.net_percent, float),
        )


class DisplayItem(BaseModel):
    id: int
    name: str
    set_name: str
    category: Category
    language: Language
    qualifiers: list[Qualifier]
    details: str | None
    purchase_date: date
    purchase_price: int
    status: Status
    intent: Intent
    grading_fee: dict[int, int]
    grading_fee_total: int
    submission_numbers: list[int]
    cracked_from: list[int]
    grade: float | None
    grading_company: GradingCompany
    cert: int | None
    list_price: float | None
    list_type: ListingType
    list_date: date | None
    sale_total: float | None
    sale_date: date | None
    shipping: float | None
    sale_fee: float | None
    usd_to_jpy_rate: float | None
    group_discount: bool
    object_variant: ObjectVariant
    audit_target: bool
    # Property values
    total_cost: int
    total_fees: float | None
    return_usd: float | None
    return_jpy: int | None
    net_jpy: int | None
    net_percent: float | None


def parse_enum(
        value: str,
        enum_cls: Type[E],
) -> E:
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_cls.__name__}: {value}')


@overload
def parse_nullable_enum(
        value: str | None,
        enum_cls: Type[E],
        as_int: Literal[True],
) -> int | None: ...


@overload
def parse_nullable_enum(
        value: str | None,
        enum_cls: Type[E],
        as_int: Literal[False] = False,
) -> E | None: ...


def parse_nullable_enum(
        value: str | None,
        enum_cls: Type[E],
        as_int: bool = False,
) -> E | int | None:
    if value == '' or value is None:
        return None
    else:
        try:
            if as_int:
                return int(enum_cls[value.upper()].value)
            else:
                return enum_cls[value.upper()]
        except KeyError:
            raise ValueError(f'Invalid {enum_cls.__name__}: {value}')


def parse_to_qualifiers_list(values: list[str] | None) -> list[Qualifier]:
    if values is None:
        return []
    else:
        return [Qualifier[x.upper()] for x in values]


def parse_nullable(
        value: str | None,
        parser: Callable[[str], T],
) -> T | None:
    if value is None or value == '':
        return None
    else:
        return parser(value)


def parse_nullable_bool(value: str | None) -> bool | None:
    if value is None or value == '':
        return None
    elif value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise ValueError(f'Invalid value passed to parse_nullable_bool: {value}')


def parse_nullable_date(date_str: str | None) -> date | None:
    if date_str is None or date_str == '':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def set_if_value(
        d: dict[str, Any],
        key: str,
        value: Any,
) -> None:
    if value is not None and value != '' and value != [] and value != {}:
        d[key] = value


def build_grading_fee_dict(
        sub_nums: list[str],
        fees: list[str],
) -> dict[int, int]:
    # Remove empty string that gets sent if multiple submissions
    sub_nums = [sn for sn in sub_nums if sn != '']
    fees = [f for f in fees if f != '']
    return {
        int(k): int(v) for k, v in zip(sub_nums, fees, strict=True)
    }


def parse_nullable_list_of_str_to_list_of_int(input_list: list[str] | None) -> list[int]:
    if input_list is None:
        return []
    else:
        # Remove empty string that gets sent if no value set
        input_list = [v for v in input_list if v != '']
        return [int(v) for v in input_list]
