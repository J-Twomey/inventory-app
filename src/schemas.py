from datetime import date
from typing import (
    Annotated,
    Any,
    Self,
)

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .helper_types import (
    E,
    T,
)
from .item_enums import (
    Category,
    GradingCompany,
    Intent,
    Language,
    ListingType,
    ObjectVariant,
    Qualifier,
    Status,
)


def enum_by_name(enum_cls: type[E]) -> BeforeValidator:
    """HTML forms send enum member names (e.g. 'PSA'), not values, so parse by name."""

    def parse(value: object) -> object:
        if isinstance(value, str):
            try:
                return enum_cls[value.upper()]
            except KeyError:
                raise ValueError(f'Invalid {enum_cls.__name__}: {value}') from None
        return value

    return BeforeValidator(parse)


class ItemBase(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        from_attributes=True,
    )

    name: str | None = None
    set_name: str | None = None
    category: Annotated[Category | None, enum_by_name(Category)] = None
    language: Annotated[Language | None, enum_by_name(Language)] = None
    qualifiers: list[Annotated[Qualifier, enum_by_name(Qualifier)]] = []
    details: str | None = None
    purchase_date: date | None = None
    purchase_price: int | None = None
    status: Annotated[Status | None, enum_by_name(Status)] = None
    intent: Annotated[Intent | None, enum_by_name(Intent)] = None
    import_fee: int | None = None
    purchase_grading_company: Annotated[
        GradingCompany | None,
        enum_by_name(GradingCompany),
    ] = None
    purchase_grade: float | None = None
    purchase_cert: int | None = None
    list_price: float | None = None
    list_type: Annotated[ListingType | None, enum_by_name(ListingType)] = None
    list_date: date | None = None
    sale_total: float | None = None
    sale_date: date | None = None
    shipping: float | None = None
    sale_fee: float | None = None
    usd_to_jpy_rate: float | None = None
    group_discount: bool = False
    object_variant: Annotated[ObjectVariant | None, enum_by_name(ObjectVariant)] = None
    audit_target: bool = False
    cracked_from_purchase: bool = False

    @classmethod
    def checkbox_fields(cls) -> set[str]:
        return {f for f, info in cls.model_fields.items() if info.annotation is bool}

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(
        cls,
        v: T,
        info: ValidationInfo,
    ) -> T | None:
        # Empty string is handled differently for these fields
        if info.field_name in {'qualifiers', *cls.checkbox_fields()}:
            return v
        if v == '':
            return None
        return v

    @field_validator('qualifiers', mode='before')
    @classmethod
    def parse_qualifiers(
        cls,
        v: object,
    ) -> object:
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        if isinstance(v, list):
            return v
        raise ValueError('Qualifiers must be provided as str or list[Qualifier]')

    @model_validator(mode='after')
    def list_date_not_before_purchase_date(self) -> Self:
        if (
            self.list_date is not None
            and self.purchase_date is not None
            and self.list_date < self.purchase_date
        ):
            raise ValueError(
                f'Listing date cannot be before purchase date '
                f'(got listing date: {self.list_date}, purchase date: {self.purchase_date})',
            )
        return self

    @model_validator(mode='after')
    def sale_date_not_before_list_date(self) -> Self:
        if (
            self.list_date is not None
            and self.sale_date is not None
            and self.sale_date < self.list_date
        ):
            raise ValueError(
                f'Sale date cannot be before listing date '
                f'(got sale date: {self.sale_date}, listing date: {self.list_date})',
            )
        return self

    @model_validator(mode='after')
    def check_required_null_fields_based_on_status(self) -> Self:
        if self.status is not None:
            not_null = [f for f in self.status.required_to_be_null if getattr(self, f) is not None]
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
        if self.list_type == ListingType.NO_LIST:
            if self.status in (Status.LISTED, Status.CLOSED):
                raise ValueError('Item cannot have list_type of NO_LIST if listed or sold')
        elif self.status not in (Status.LISTED, Status.CLOSED):
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
        if self.audit_target and self.status in (Status.CLOSED, Status.LISTED):
            raise ValueError('Item assigned as an audit target can not be listed or closed')
        return self


class ItemCreate(ItemBase):
    name: str
    set_name: str
    category: Annotated[Category, enum_by_name(Category)]
    language: Annotated[Language, enum_by_name(Language)]
    purchase_date: date
    purchase_price: int
    status: Annotated[Status, enum_by_name(Status)]
    intent: Annotated[Intent, enum_by_name(Intent)]
    import_fee: int
    purchase_grading_company: Annotated[GradingCompany, enum_by_name(GradingCompany)]
    list_type: Annotated[ListingType, enum_by_name(ListingType)]
    object_variant: Annotated[ObjectVariant, enum_by_name(ObjectVariant)]

    def to_model_kwargs(
        self,
        exclude: set[str] | None = None,
    ) -> dict[str, Any]:
        return self.model_dump(exclude=exclude)

    @model_validator(mode='after')
    def check_required_fields_based_on_status(self) -> Self:
        missing = [f for f in self.status.required_fields if getattr(self, f) is None]
        if len(missing) > 0:
            raise ValueError(
                f'Status {self.status.name} requires the following missing fields: {missing}',
            )
        return self

    @model_validator(mode='after')
    def appropriate_status_based_on_intent(self) -> Self:
        if self.status not in self.intent.allowed_statuses:
            raise ValueError(
                f'Item can not have status of {self.status.name} with intent of '
                f'{self.intent.name}',
            )
        return self


class ItemUpdate(ItemBase):
    @model_validator(mode='before')
    @classmethod
    def default_unchecked_checkboxes(cls, data: object) -> object:
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
            for checkbox in cls.checkbox_fields():
                data.setdefault(checkbox, False)
        return data

    def to_model_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class ItemSearch(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str | None = None
    set_name: str | None = None
    category: Annotated[Category | None, enum_by_name(Category)] = None
    language: Annotated[Language | None, enum_by_name(Language)] = None
    qualifiers: list[Annotated[Qualifier, enum_by_name(Qualifier)]] = []
    details: str | None = None
    purchase_date_min: date | None = None
    purchase_date_max: date | None = None
    purchase_price_min: int | None = None
    purchase_price_max: int | None = None
    status: Annotated[Status | None, enum_by_name(Status)] = None
    intent: Annotated[Intent | None, enum_by_name(Intent)] = None
    cracked_from_purchase: bool | None = None
    grading_company: Annotated[GradingCompany | None, enum_by_name(GradingCompany)] = None
    grade: float | None = None
    cert: int | None = None
    list_type: Annotated[ListingType | None, enum_by_name(ListingType)] = None
    list_date_min: date | None = None
    list_date_max: date | None = None
    sale_total_min: float | None = None
    sale_total_max: float | None = None
    sale_date_min: date | None = None
    sale_date_max: date | None = None
    group_discount: bool | None = None
    object_variant: Annotated[ObjectVariant | None, enum_by_name(ObjectVariant)] = None
    audit_target: bool | None = None
    total_cost_min: int | None = None
    total_cost_max: int | None = None
    return_jpy_min: int | None = None
    return_jpy_max: int | None = None
    net_jpy_min: int | None = None
    net_jpy_max: int | None = None
    net_percent_min: float | None = None
    net_percent_max: float | None = None

    @model_validator(mode='before')
    @classmethod
    def treat_empty_fields_as_unset(cls, data: object) -> object:
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None and v != ''}
        return data


class ItemForSubmissionForm(BaseModel):
    """
    This is necessary for usage with javascript to provide nicely formatted strings that can be
    used as is in the display. If further information about an item is required it can be added
    here.
    """

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

    @model_validator(mode='after')
    def return_date_not_before_submission_date(self) -> Self:
        if (
            self.submission_date is not None
            and self.return_date is not None
            and self.return_date < self.submission_date
        ):
            raise ValueError(
                f'Return date cannot be before submission date '
                f'(got return date: {self.return_date}, '
                f'submission date: {self.submission_date})',
            )
        return self

    @model_validator(mode='after')
    def break_even_date_not_before_return_date(self) -> Self:
        if (
            self.return_date is not None
            and self.break_even_date is not None
            and self.break_even_date < self.return_date
        ):
            raise ValueError(
                f'Break even date cannot be before return date '
                f'(got break even date: {self.break_even_date}, '
                f'return date: {self.return_date})',
            )
        return self


class SubmissionCreate(SubmissionBase):
    submission_number: int
    submission_company: GradingCompany

    def to_model_kwargs(self) -> dict[str, int | date | None]:
        return self.model_dump()


class GradingRecordBase(BaseModel):
    model_config = ConfigDict(extra='forbid')

    item_id: int | None = None
    submission_id: int | None = None
    grading_fee: int | None = None
    grade: float | None = None
    cert: int | None = None
    is_cracked: bool = False

    @classmethod
    def checkbox_fields(cls) -> set[str]:
        return {f for f, info in cls.model_fields.items() if info.annotation is bool}


class GradingRecordCreate(GradingRecordBase):
    item_id: int
    submission_id: int

    def to_model_kwargs(self) -> dict[str, int | float | bool | None]:
        return self.model_dump()


class GradingRecordUpdate(GradingRecordBase):
    @model_validator(mode='before')
    @classmethod
    def treat_empty_fields_as_unset(cls, data: object) -> object:
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None and v != ''}
            for checkbox in cls.checkbox_fields():
                data.setdefault(checkbox, False)
        return data

    def to_model_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)
