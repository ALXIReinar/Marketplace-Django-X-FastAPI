from fastapi import APIRouter, Request

from core.bg_tasks.celery_processing import lvl1_render
from core.config_dir.debug_logger import log_debug
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.config_dir.base_dependencies import PagenDep
from core.utils.anything import Tags, Events

router = APIRouter(prefix='/api/products', tags=[Tags.products])



@router.post('/', summary="Выдать Карточки товаров")
async def preview_products(pagen: PagenDep, request: Request, db: PgSqlDep):
    if hasattr(request.state, 'user_id'):
        user_id = request.state.user_id
    else: user_id = 1

    records = await db.products.welcome_page_select(user_id, pagen.offset, pagen.limit)
    return {'products': records.products,
            'counters': [
                {'favorite': records.favorite}, {'ordered_items': records.ordered_items}]
            }



@router.get('/{prd_id}_{seller_id}')
async def get_product_card(
        request: Request, db: PgSqlDep,
        prd_id: int,
        seller_id: int,
        in_front_cache: bool = False
):


    product_inst_part = 'cached'
    if not in_front_cache:
        log_event(Events.bg_product_stage_.format('0' + ' | NO cached'), request, level='WARNING')
        product_inst_part = await db.extended_product.instant_data_product_heavy(prd_id)
    else:    log_event(Events.bg_product_stage_.format('0' + ' | cached!'), request)
    task = lvl1_render.apply_async(args=[prd_id, in_front_cache])
    return {'task-bg_lvl_1': task.id, 'product_info': product_inst_part}


