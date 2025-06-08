from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config_dir.base_dependencies import PagenDep, PagenSearchDep
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.utils.anything import Tags

router = APIRouter(prefix='/api/orders', tags=[Tags.orders])



@router.get('/')
async def orders_frame_tab(request: Request, db: PgSqlDep):
    if request.state.user_id == 1:
        return JSONResponse(status_code=200, content={'success': False, 'message': 'Войдите в аккаунт'})
    actual_count, complete_count, purchase_count = await db.products.orders_counters(request.state.user_id)
    return {'success': True, 'orders_counts':{
        'actual': actual_count,
        'completed': complete_count,
        'purchased': purchase_count
    }}

@router.get('/sections', summary="В статус:  'Актуальные' либо 'Завершённые' => True и False соответственно")
async def orders_list(status: bool, pagen: PagenDep, request: Request, db: PgSqlDep):
    """
    в будущем подрубить редис, если будет находить < 60 записей, чтобы быстро фильтровать
    """
    records = await db.products.orders_product_list(request.state.user_id, status, pagen.limit, pagen.offset)
    log_event("Отображено заказанных товаров: %s; user_id: %s; status: %s", len(records), request.state.user_id, status, request=request)
    return {'order_products': records}


@router.get('/purchased')
async def buy_again(pagen: PagenSearchDep, request: Request, db: PgSqlDep):
    products = await db.products.purchased_prds(request.state.user_id, pagen.limit, pagen.offset)
    return {'purchased_products': products}
