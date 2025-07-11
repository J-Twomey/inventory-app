from fastapi import (
    APIRouter,
    Depends,
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
    delete_item_by_id,
    edit_item,
    get_all_submission_values,
    get_newest_items,
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
from .models import Item
from .schemas import (
    ItemCreateForm,
    ItemSearchForm,
    ItemUpdateForm,
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
def show_add_form(request: Request) -> Response:
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
def submit_add_form(
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
def open_edit_form(
        item_id: int,
        request: Request,
        db: Session = Depends(get_db),
) -> Response:
    item = db.query(Item).filter(Item.id == item_id).first()
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
