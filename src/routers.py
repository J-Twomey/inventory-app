from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import Response

from .crud import (
    create_item,
    create_submission,
    delete_item_by_id,
    delete_submission_by_id,
    edit_item,
    edit_submission,
    get_all_submission_values,
    get_item,
    get_newest_items,
    get_newest_submissions,
    get_submission,
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
    ItemCreateForm,
    ItemDisplay,
    ItemSearchForm,
    ItemUpdateForm,
    SubmissionCreate,
    SubmissionUpdateForm,
)


templates = Jinja2Templates(directory='templates')
router = APIRouter()


@router.get('/', response_class=HTMLResponse)
def read_root(request: Request) -> Response:
    return templates.TemplateResponse('index.html', {'request': request})


@router.get('/view', response_class=HTMLResponse)
def view_items(
        request: Request,
        db: Session = Depends(get_db),
        search_form: ItemSearchForm = Depends(ItemSearchForm.as_query),
        show_limit: int = 20,
) -> Response:
    search_data = search_form.to_item_search()
    search_values = {
        k: v for k, v in search_data.model_dump(exclude_none=True).items()
        if not (isinstance(v, list) and not v)
    }
    if not search_values:
        items = get_newest_items(db, skip=0, limit=show_limit)
    else:
        items = search_for_items(db, search_data)
        items = items[:show_limit]
    display_items = [item.to_display() for item in items]
    submission_options = get_all_submission_values(db)
    return templates.TemplateResponse(
        'view.html',
        {
            'request': request,
            'items': display_items,
            'form_data': search_form,
            'qualifier_enum': Qualifier,
            'category_enum': Category,
            'language_enum': Language,
            'status_enum': Status,
            'intent_enum': Intent,
            'grading_company_enum': GradingCompany,
            'list_type_enum': ListingType,
            'object_variant_enum': ObjectVariant,
            'submission_options': submission_options,
        },
    )


@router.get('/add')
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


@router.post('/add')
def submit_add_item_form(
        form: ItemCreateForm = Depends(ItemCreateForm.as_form),
        db: Session = Depends(get_db),
) -> RedirectResponse:
    item = form.to_item_create()
    create_item(db, item)
    return RedirectResponse(url='/view', status_code=303)


@router.get('/delete/{item_id}')
def delete_item(
        item_id: int,
        db: Session = Depends(get_db),
) -> RedirectResponse:
    success = delete_item_by_id(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail='Item not found')
    return RedirectResponse(url='/view', status_code=303)


@router.get('/edit/{item_id}', response_class=HTMLResponse)
def open_edit_item_form(
        item_id: int,
        request: Request,
        db: Session = Depends(get_db),
) -> Response:
    item = get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='Item not found')
    else:
        display_item = item.to_display()
    return templates.TemplateResponse(
        'edit_item.html',
        {
            'request': request,
            'item': display_item,
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
    return RedirectResponse('/view', status_code=edit_result)


@router.get('/submissions_view', response_class=HTMLResponse)
def view_submissions(
        request: Request,
        db: Session = Depends(get_db),
        show_limit: int = 20,
) -> Response:
    submissions = get_newest_submissions(db, skip=0, limit=show_limit)
    display_submissions = [sub.to_display() for sub in submissions]
    return templates.TemplateResponse(
        'submissions_view.html',
        {
            'request': request,
            'submissions': display_submissions,
        },
    )


@router.get('/submissions_add')
def show_add_submission_form(request: Request) -> Response:
    return templates.TemplateResponse(
        'add_submission.html',
        {
            'request': request,
            'grading_company_enum': GradingCompany,
        },
    )


@router.post('/submissions_add')
def submit_add_submission_form(
        request: Request,
        submission_number: int = Form(...),
        submission_company: str = Form(...),
        item_ids: list[int] = Form(...),
        db: Session = Depends(get_db),
) -> Response:
    submissions = [
        SubmissionCreate(
            item_id=i,
            submission_number=submission_number,
            submission_company=GradingCompany[submission_company],
        )
        for i in item_ids
    ]
    try:
        create_submission(db, submissions)
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
    return RedirectResponse(url='/submissions_view', status_code=303)


@router.get('/item_info_for_submission_form/{item_id}')
def get_item_info_for_submission_form(
        item_id: int,
        db: Session = Depends(get_db),
) -> ItemDisplay:
    item = get_item(db, item_id)
    if item is None:
        return ItemDisplay(id=item_id, name='N/A')
    else:
        return item.to_display()


@router.get('/submissions_delete/{submission_id}')
def delete_submission(
        submission_id: int,
        db: Session = Depends(get_db),
) -> RedirectResponse:
    success = delete_submission_by_id(db, submission_id)
    if not success:
        raise HTTPException(status_code=404, detail='Submission not found')
    return RedirectResponse(url='/submissions_view', status_code=303)


@router.get('/submissions_edit/{submission_id}', response_class=HTMLResponse)
def open_edit_submission_form(
        submission_id: int,
        request: Request,
        db: Session = Depends(get_db),
) -> Response:
    submission = get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail='Submission not found')
    else:
        display_submission = submission.to_display()
    return templates.TemplateResponse(
        'edit_submission.html',
        {
            'request': request,
            'submission': display_submission,
            'grading_company_enum': GradingCompany,
        },
    )


@router.post('/submissions_edit/{submission_id}')
def submit_edit_submission(
        submission_id: int,
        update_form: SubmissionUpdateForm = Depends(SubmissionUpdateForm.as_form),
        db: Session = Depends(get_db),
) -> RedirectResponse:
    edit_params = update_form.to_submission_update()
    edit_result = edit_submission(db, submission_id, edit_params)
    return RedirectResponse('/submissions_view', status_code=edit_result)
