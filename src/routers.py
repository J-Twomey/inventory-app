from datetime import date

from typing import TypedDict

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
    get_newest_items,
    get_newest_submissions,
    get_newest_grading_records,
    get_total_number_of_items,
    search_for_items,
)
from .database import get_db
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
from .schemas import (
    E,
    GradingRecordCreate,
    GradingRecordUpdateForm,
    ItemCreateForm,
    ItemForSubmissionForm,
    ItemSearchForm,
    ItemUpdateForm,
    parse_nullable_date,
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
        items = items[-(skip + show_limit): -skip if skip != 0 else None]

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
            'skip': skip,
            'prev_url': prev_url,
            'next_url': next_url,
        },
    )


@router.get('/add_item')
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
) -> Response:
    show_limit = max(1, min(show_limit, 500))
    submissions = get_newest_submissions(db, skip=0, limit=show_limit)
    return templates.TemplateResponse(
        'submissions_summary_view.html',
        {
            'request': request,
            'submission_summaries': submissions,
            'show_limit': show_limit,
        },
    )


class SubmissionTableUpdatePayload(TypedDict, total=False):
    submission_number: int
    field: str
    value: str


@router.post('/submissions_summary_edit')
def update_submission_summary_field(
        payload: SubmissionTableUpdatePayload = Body(...),
        db: Session = Depends(get_db),
) -> JSONResponse:
    submission_number = payload['submission_number']
    field = payload['field']
    update_value = parse_nullable_date(payload['value'])

    edit_result = edit_submission_single_field(db, submission_number, field, update_value)
    return JSONResponse({'status_code': edit_result})


@router.get('/grading_records_view', response_class=HTMLResponse)
def view_grading_records(
        request: Request,
        db: Session = Depends(get_db),
        show_limit: int = 20,
) -> Response:
    show_limit = max(1, min(show_limit, 500))
    grading_records = get_newest_grading_records(db, skip=0, limit=show_limit)
    return templates.TemplateResponse(
        'grading_records_view.html',
        {
            'request': request,
            'records': grading_records,
            'show_limit': show_limit,
        },
    )


@router.get('/add_submission')
def show_add_submission_form(request: Request) -> Response:
    return templates.TemplateResponse(
        'add_submission.html',
        {
            'request': request,
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
    records = [
        GradingRecordCreate(
            item_id=i,
            submission_number=submission_number,
        )
        for i in item_ids
    ]
    try:
        create_submission(db, submission_summary, records)
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
templates.env.filters['grading_company_enum'] = format_grading_company_enum
