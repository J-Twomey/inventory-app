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
            exclude: set[str] = set()) -> dict[str, Any]:
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
    grading_fee: str
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
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date=purchase_date_,
            purchase_price=int(self.purchase_price),
            status=parse_enum(self.status, Status, 'status'),
            intent=parse_enum(self.intent, Intent, 'intent'),
            grading_fee=parse_to_dict(self.grading_fee or '{}'),
            grade=parse_nullable(self.grade, float),
            grading_company=parse_enum(self.grading_company, GradingCompany, 'grading_company'),
            cert=parse_nullable(self.cert, int),
            list_price=parse_nullable(self.list_price, float),
            list_type=parse_enum(self.list_type, ListingType, 'list_type'),
            list_date=list_date_,
            sale_total=parse_nullable(self.sale_total, float),
            sale_date=sale_date_,
            shipping=parse_nullable(self.shipping, float),
            sale_fee=parse_nullable(self.sale_fee, float),
            usd_to_jpy_rate=parse_nullable(self.usd_to_jpy_rate, float),
            group_discount=self.group_discount,
            object_variant=parse_enum(self.object_variant, ObjectVariant, 'object_variant'),
            audit_target=self.audit_target,
        )


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str | None = None
    set_name: str | None = None
    category: Category | None = None
    language: Language | None = None
    qualifiers: list[Qualifier] | None = None
    details: str | None = None
    purchase_date: date | None = None
    purchase_price: int | None = None
    status: Status | None = None
    intent: Intent | None = None
    grading_fee: dict[int, int] | None = None
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


@dataclass
class ItemUpdateForm:
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

    @classmethod
    def as_form(
        cls,
        name: Annotated[str | None, Form()] = None,
        set_name: Annotated[str | None, Form()] = None,
        category: Annotated[str | None, Form()] = None,
        language: Annotated[str | None, Form()] = None,
        qualifiers: Annotated[list[str] | None, Form()] = None,
        details: Annotated[str | None, Form()] = None,
        purchase_date: Annotated[str | None, Form()] = None,
        purchase_price: Annotated[str | None, Form()] = None,
        status: Annotated[str | None, Form()] = None,
        intent: Annotated[str | None, Form()] = None,
        grading_fee: Annotated[str | None, Form()] = None,
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
            grading_fee=grading_fee,
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
            group_discount=group_discount,
            object_variant=object_variant,
            audit_target=audit_target,
        )

    def to_item_update(self) -> ItemUpdate:
        update_vals: dict[str, Any] = {}
        set_if_value(update_vals, 'name', parse_nullable(self.name, str))
        set_if_value(update_vals, 'set_name', parse_nullable(self.set_name, str))
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
        set_if_value(update_vals, 'details', parse_nullable(self.details, str))
        set_if_value(update_vals, 'purchase_date', parse_nullable_date(self.purchase_date))
        set_if_value(update_vals, 'purchase_price', parse_nullable(self.purchase_price, int))
        set_if_value(update_vals, 'status', parse_nullable_enum(self.status, Status, 'status'))
        set_if_value(update_vals, 'intent', parse_nullable_enum(self.intent, Intent, 'intent'))
        set_if_value(update_vals, 'grading_fee', parse_to_nullable_dict(self.grading_fee))
        set_if_value(update_vals, 'grade', parse_nullable(self.grade, float))
        set_if_value(
            update_vals,
            'grading_company',
            parse_nullable_enum(self.grading_company, GradingCompany, 'grading_company'),
        )
        set_if_value(update_vals, 'cert', parse_nullable(self.cert, int))
        set_if_value(update_vals, 'list_price', parse_nullable(self.list_price, float))
        set_if_value(
            update_vals,
            'list_type',
            parse_nullable_enum(self.list_type, ListingType, 'list_type'),
        )
        set_if_value(update_vals, 'list_date', parse_nullable_date(self.list_date))
        set_if_value(update_vals, 'sale_total', parse_nullable(self.sale_total, float))
        set_if_value(update_vals, 'sale_date', parse_nullable_date(self.sale_date))
        set_if_value(update_vals, 'shipping', parse_nullable(self.shipping, float))
        set_if_value(update_vals, 'sale_fee', parse_nullable(self.sale_fee, float))
        set_if_value(update_vals, 'usd_to_jpy', parse_nullable(self.usd_to_jpy, float))
        set_if_value(update_vals, 'group_discount', self.group_discount)
        set_if_value(
            update_vals,
            'object_variant',
            parse_nullable_enum(self.object_variant, ObjectVariant, 'object_variant'),
        )
        set_if_value(update_vals, 'audit_target', self.audit_target)
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
            category=parse_enum_as_int(self.category, Category, 'category'),
            language=parse_enum_as_int(self.language, Language, 'language'),
            qualifiers=parse_to_qualifiers_list(self.qualifiers),
            details=parse_nullable(self.details, str),
            purchase_date=purchase_date_,
            purchase_price=parse_nullable(self.purchase_price, int),
            status=parse_enum_as_int(self.status, Status, 'status'),
            intent=parse_enum_as_int(self.intent, Intent, 'intent'),
            grade=parse_nullable(self.grade, float),
            grading_company=parse_enum_as_int(
                self.grading_company,
                GradingCompany,
                'grading_company',
            ),
            cert=parse_nullable(self.cert, int),
            list_type=parse_enum_as_int(self.list_type, ListingType, 'listing_type'),
            list_date=list_date_,
            sale_total=parse_nullable(self.sale_total, float),
            sale_date=sale_date_,
            group_discount=parse_nullable_bool(self.group_discount),
            object_variant=parse_enum_as_int(self.object_variant, ObjectVariant, 'object_variant'),
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
        enum_name: str,
) -> E:
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_name}: {value}')


def parse_nullable_enum(
        value: str | None,
        enum_cls: Type[E],
        enum_name: str,
) -> E | None:
    if value == '' or value is None:
        return None
    else:
        try:
            return enum_cls[value.upper()]
        except KeyError:
            raise ValueError(f'Invalid {enum_name}: {value}')


def parse_enum_as_int(
        value: str | None,
        enum_cls: Type[E],
        enum_name: str,
) -> int | None:
    if value == '' or value is None:
        return None
    else:
        try:
            return int(enum_cls[value.upper()].value)
        except KeyError:
            raise ValueError(f'Invalid {enum_name}: {value}')


def parse_to_qualifiers_list(values: list[str] | None) -> list[Qualifier]:
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


def parse_nullable(
        value: str | None,
        parser: Callable[[str], T],
) -> T | None:
    if value is None or value == '':
        return None
    else:
        return parser(value)


def parse_nullable_bool(v: str | None) -> bool | None:
    if v is None or v == '':
        return None
    elif v.lower() == 'true':
        return True
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
