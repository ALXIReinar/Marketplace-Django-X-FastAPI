from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config_dir.base_dependencies import PagenFavoriteDep
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.utils.anything import Tags

router = APIRouter(prefix='/api/favorites', tags=[Tags.favorites])


@router.get('/')
async def favorite_list(pagen: PagenFavoriteDep, request: Request, db: PgSqlDep):
    """
    в будущем подрубить редис, если будет находить < 20 записей, чтобы быстро фильтровать
    """
    if request.state.user_id == 1:
        return JSONResponse(status_code=200, content={'message': 'Войдите в аккаунт'})

    records = await db.products.favorite_product_list(request.state.user_id, pagen.limit, pagen.offset)
    log_event("Отображено товаров в избранном: %s; user_id: %s", len(records), request.state.user_id, request=request)
    return {'favorite_products': records}
