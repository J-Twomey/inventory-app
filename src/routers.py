from datetime import date

from typing import (
    Sequence,
    TypedDict,
)

from fastapi import (
    APIRouter,
    Body,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response

from .crud import (
    create_item,
    create_submission,
    delete_item_by_id,
    delete_grading_record_by_id,
    edit_grading_record,
    edit_item,
    edit_submission_single_field,
    get_grading_record,
    get_item,
    get_max_sub_number,
    get_newest_items,
    get_newest_submissions,
    get_newest_grading_records,
    get_total_number_of_grading_records,
    get_total_number_of_items,
    get_total_number_of_submissions,
    search_for_items,
    SubmissionNotFound,
    SubmissionNumberConflict,
)
from .database import get_db
from .helper_types import E
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
from .models import Item
from .parsers import parse_submission_update_field
from .schemas import (
    GradingRecordUpdateForm,
    ItemCreateForm,
    ItemForSubmissionForm,
    ItemSearchForm,
    ItemUpdateForm,
    SubmissionCreate,
)


templates = Jinja2Templates(directory='templates')
router = APIRouter()


@router.get('/', response_class=HTMLResponse)
def read_root(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/items_view', response_class=HTMLResponse)
def view_items(
    request: Request,
    db: Session = Depends(get_db),
    search_form: ItemSearchForm = Depends(ItemSearchForm.as_query),
    show_limit: int = 20,
    skip: int = 0,
    selection_mode: bool = False,
) -> Response:
    show_limit = max(1, min(show_limit, 500))
    skip = max(0, skip)
    search_data = search_form.to_item_search()
    search_values = {
        k: v for k, v in search_data.model_dump(exclude_none=True).items()
        if not (isinstance(v, list) and not v)
    }
    if not search_values:
        num_results = get_total_number_of_items(db)
        items = get_newest_items(db, skip=skip, limit=show_limit)
    else:
        items = search_for_items(db, search_data)
        num_results = len(items)
        items = slice_items(items, skip, show_limit)

    prev_url, next_url = generate_page_urls(
        request=request,
        skip=skip,
        show_limit=show_limit,
        num_results=num_results,
    )
    return templates.TemplateResponse(
        'items_view.html',
        {
            'request': request,
            'items': items,
            'form_data': search_form,
            'qualifier_enum': Qualifier,
            'category_enum': Category,
            'language_enum': Language,
            'status_enum': Status,
            'intent_enum': Intent,
            'grading_company_enum': GradingCompany,
            'list_type_enum': ListingType,
            'object_variant_enum': ObjectVariant,
            'show_limit': show_limit,
            'prev_url': prev_url,
            'next_url': next_url,
            'selection_mode': selection_mode,
        },
    )


@router.get('/add_item', response_class=HTMLResponse)
def show_add_item_form(request: Request) -> Response:
    return templates.TemplateResponse(
        'add_item.html',
        {
            'request': request,
            'qualifier_enum': Qualifier,
            'category_enum': Category,
            'language_enum': Language,
            'status_enum': Status,
            'intent_enum': Intent,
            'grading_company_enum': GradingCompany,
            'list_type_enum': ListingType,
            'object_variant_enum': ObjectVariant,
        },
    )


@router.post('/add_item')
def submit_add_item_form(
    form: ItemCreateForm = Depends(ItemCreateForm.as_form),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    item = form.to_item_create()
    create_item(db, item)
    return RedirectResponse(url='/items_view', status_code=303)


@router.get('/delete/{item_id}')
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    success = delete_item_by_id(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail='Item not found')
    return RedirectResponse(url='/items_view', status_code=303)


@router.get('/edit/{item_id}', response_class=HTMLResponse)
def open_edit_item_form(
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    item = get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Item not found')
    return templates.TemplateResponse(
        'edit_item.html',
        {
            'request': request,
            'item': item,
            'qualifier_enum': Qualifier,
            'category_enum': Category,
            'language_enum': Language,
            'status_enum': Status,
            'intent_enum': Intent,
            'grading_company_enum': GradingCompany,
            'list_type_enum': ListingType,
            'object_variant_enum': ObjectVariant,
        },
    )


@router.post('/edit/{item_id}')
def submit_edit_item(
    item_id: int,
    update_form: ItemUpdateForm = Depends(ItemUpdateForm.as_form),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    edit_params = update_form.to_item_update()
    edit_result = edit_item(db, item_id, edit_params)
    return RedirectResponse('/items_view', status_code=edit_result)


@router.get('/submissions_summary_view', response_class=HTMLResponse)
def view_submissions_summary(
    request: Request,
    db: Session = Depends(get_db),
    show_limit: int = 20,
    skip: int = 0,
) -> Response:
    show_limit = max(1, min(show_limit, 500))
    num_results = get_total_number_of_submissions(db)
    submissions = get_newest_submissions(db, skip=skip, limit=show_limit)
    prev_url, next_url = generate_page_urls(
        request=request,
        skip=skip,
        show_limit=show_limit,
        num_results=num_results,
    )
    return templates.TemplateResponse(
        'submissions_summary_view.html',
        {
            'request': request,
            'submission_summaries': submissions,
            'show_limit': show_limit,
            'prev_url': prev_url,
            'next_url': next_url,
            'grading_company_enum': GradingCompany,
        },
    )


class SubmissionTableUpdatePayload(TypedDict, total=False):
    submission_id: int
    field: str
    value: str


@router.post('/submissions_summary_edit')
def update_submission_summary_field(
    payload: SubmissionTableUpdatePayload = Body(...),
    db: Session = Depends(get_db),
) -> JSONResponse:
    submission_id = payload['submission_id']
    field = payload['field']
    update_value = parse_submission_update_field(field, payload['value'])

    try:
        edit_submission_single_field(db, submission_id, field, update_value)
        return JSONResponse(
            status_code=200,
            content={'success': True},
        )
    except SubmissionNotFound:
        return JSONResponse(
            status_code=404,
            content={
                'success': False,
                'error_message': 'Submission not found',
            },
        )
    except SubmissionNumberConflict:
        return JSONResponse(
            status_code=409,
            content={
                'success': False,
                'error_message': 'Provided submission number is already in use or is negative',
            },
        )


@router.get('/grading_records_view', response_class=HTMLResponse)
def view_grading_records(
    request: Request,
    db: Session = Depends(get_db),
    show_limit: int = 20,
    skip: int = 0,
) -> Response:
    show_limit = max(1, min(show_limit, 500))
    num_results = get_total_number_of_grading_records(db)
    grading_records = get_newest_grading_records(db, skip=skip, limit=show_limit)
    prev_url, next_url = generate_page_urls(
        request=request,
        skip=skip,
        show_limit=show_limit,
        num_results=num_results,
    )
    return templates.TemplateResponse(
        'grading_records_view.html',
        {
            'request': request,
            'records': grading_records,
            'show_limit': show_limit,
            'prev_url': prev_url,
            'next_url': next_url,
        },
    )


@router.get('/add_submission', response_class=HTMLResponse)
def show_add_submission_form(
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    current_max_sub_number = get_max_sub_number(db)
    return templates.TemplateResponse(
        'add_submission.html',
        {
            'request': request,
            'next_new_sub_num': current_max_sub_number + 1,
            'grading_company_enum': GradingCompany,
        },
    )


@router.post('/add_submission')
def submit_add_submission_form(
    request: Request,
    submission_number: int = Form(...),
    submission_company: str = Form(...),
    submission_date: str = Form(...),
    item_ids: list[int] = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    if submission_date == '':
        parsed_date = None
    else:
        parsed_date = date.fromisoformat(submission_date)
    submission_summary = SubmissionCreate(
        submission_number=submission_number,
        submission_company=GradingCompany[submission_company],
        submission_date=parsed_date,
        return_date=None,
        break_even_date=None,
    )
    try:
        create_submission(db, submission_summary, item_ids)
    except ValueError as e:
        error_message = str(e)
        return templates.TemplateResponse(
            'add_submission.html',
            {
                'request': request,
                'item_ids': item_ids,
                'submission_number': submission_number,
                'submission_company': submission_company,
                'grading_company_enum': GradingCompany,
                'error_message': error_message,
            },
        )
    return RedirectResponse(url='/grading_records_view?submitted=1', status_code=303)


@router.get('/items_lookup', response_class=HTMLResponse)
def items_lookup(
    request: Request,
    db: Session = Depends(get_db),
    search_form: ItemSearchForm = Depends(ItemSearchForm.as_query),
    show_limit: int = 20,
    skip: int = 0,
    selection_mode: bool = True,
) -> Response:
    search_data = search_form.to_item_search()

    if search_data.status is None:
        search_data.status = Status.STORAGE
    if search_data.intent is None:
        search_data.intent = Intent.GRADE

    items = search_for_items(db, search_data)
    num_results = len(items)
    items = slice_items(items, skip, show_limit)
    prev_url, next_url = generate_page_urls(
        request=request,
        skip=skip,
        show_limit=show_limit,
        num_results=num_results,
    )
    return templates.TemplateResponse(
        'items_lookup.html',
        {
            'request': request,
            'items': items,
            'form_data': search_form,
            'qualifier_enum': Qualifier,
            'category_enum': Category,
            'language_enum': Language,
            'status_enum': Status,
            'intent_enum': Intent,
            'grading_company_enum': GradingCompany,
            'show_limit': show_limit,
            'prev_url': prev_url,
            'next_url': next_url,
            'num_results': num_results,
            'selection_mode': selection_mode,
        },
    )


@router.get('/item_info_for_submission_form/{item_id}', response_model=ItemForSubmissionForm)
def get_item_info_for_submission_form(
    item_id: int,
    db: Session = Depends(get_db),
) -> ItemForSubmissionForm:
    item = get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Item not found')
    else:
        return ItemForSubmissionForm(
            name=item.name,
            set_name=item.set_name,
            category=item.category.name.replace('_', ' ').title(),
            language=item.language.name.replace('_', ' ').title(),
            intent=item.intent.name.replace('_', ' ').title(),
            purchase_date=item.purchase_date,
            purchase_price=item.purchase_price,
            status=item.status.name.replace('_', ' ').title(),
            qualifiers=[q.name.replace('_', ' ').title() for q in item.qualifiers],
            details=item.details,
        )


@router.get('/grading_record_delete/{grading_record_id}')
def delete_submission_item(
    grading_record_id: int,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    success = delete_grading_record_by_id(db, grading_record_id)
    if not success:
        raise HTTPException(status_code=404, detail='Grading record not found')
    return RedirectResponse(url='/grading_records_view', status_code=303)


@router.get('/grading_record_edit/{grading_record_id}', response_class=HTMLResponse)
def open_edit_grading_record_form(
    grading_record_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    record = get_grading_record(db, grading_record_id)
    if record is None:
        raise HTTPException(status_code=404, detail='Grading_record not found')
    return templates.TemplateResponse(
        'edit_grading_record.html',
        {
            'request': request,
            'record': record,
            'grading_company_enum': GradingCompany,
        },
    )


@router.post('/grading_record_edit/{grading_record_id}')
def submit_edit_grading_record(
    grading_record_id: int,
    update_form: GradingRecordUpdateForm = Depends(GradingRecordUpdateForm.as_form),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    edit_params = update_form.to_grading_record_update()
    edit_result = edit_grading_record(db, grading_record_id, edit_params)
    return RedirectResponse('/grading_records_view', status_code=edit_result)


def slice_items(
    items: Sequence[Item],
    skip: int,
    show_limit: int,
) -> Sequence[Item]:
    return items[-(skip + show_limit): -skip if skip != 0 else None]


def generate_page_urls(
    request: Request,
    skip: int,
    show_limit: int,
    num_results: int,
) -> tuple[str, str]:
    if skip + show_limit < num_results:
        prev_url = str(request.url.include_query_params(skip=skip + show_limit))
    else:
        prev_url = 'none'

    if skip > 0:
        next_url = str(request.url.include_query_params(skip=max(0, skip - show_limit)))
    else:
        next_url = 'none'
    return prev_url, next_url


def format_dollar(value: float | None) -> str:
    if value is None:
        return ''
    return f'${value:,.2f}'


def format_yen(value: float | None) -> str:
    if value is None:
        return ''
    return f'¥{value:,.0f}'


def format_percent(value: float | None) -> str:
    if value is None:
        return ''
    return f'{value:,.2f}%'


def format_enum(e: E) -> str:
    return e.name.title() if e else ''


def format_grading_company_enum(e: GradingCompany) -> str:
    return e.name if e else ''


templates.env.filters['dollar'] = format_dollar
templates.env.filters['yen'] = format_yen
templates.env.filters['percent'] = format_percent
templates.env.filters['enum'] = format_enum
templates.env.filters['grading_company_enum_format'] = format_grading_company_enum
