from fastapi import APIRouter, Request

from core.config_dir.base_dependencies import PagenDep
from core.config_dir.logger import Tags
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import UserBase

router = APIRouter(prefix='/api/products')



@router.post('/', tags=[Tags.products], summary="Выдать Карточки товаров")
async def preview_products(user: UserBase, pagen: PagenDep, request: Request, db: PgSqlDep):
    if hasattr(request.cookies, 'user_id'):
        user_id = request.state.user_id
    else: user_id = user.id

    records = await db.welcome_page_select(user_id, pagen.offset, pagen.limit)
    return {'products': records.products,
            'counters': [
                {'favorite': records.favorite}, {'ordered_items': records.ordered_items}]
            }