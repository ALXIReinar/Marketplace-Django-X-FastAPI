from fastapi import APIRouter, Request

from core.config_dir.base_dependencies import PagenDep
from core.utils.anything import Tags
from core.db_data.postgre import PgSqlDep

router = APIRouter(prefix='/api/products')



@router.post('/', tags=[Tags.products], summary="Выдать Карточки товаров")
async def preview_products(pagen: PagenDep, request: Request, db: PgSqlDep):
    if hasattr(request.state, 'user_id'):
        user_id = request.state.user_id
    else: user_id = 1

    records = await db.welcome_page_select(user_id, pagen.offset, pagen.limit)
    return {'products': records.products,
            'counters': [
                {'favorite': records.favorite}, {'ordered_items': records.ordered_items}]
            }