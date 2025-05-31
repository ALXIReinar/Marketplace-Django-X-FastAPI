from celery.result import AsyncResult
from fastapi import APIRouter, Request

from core.bg_tasks.celery_processing import lvl1_render, lvl2_render, lvl3_render
from core.config_dir.debug_logger import log_debug
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.config_dir.base_dependencies import PagenDep
from core.utils.anything import Tags, Events

router = APIRouter(prefix='/api/products', tags=[Tags.products])



@router.post('/', summary="Выдать Карточки товаров")
async def preview_products(pagen: PagenDep, request: Request, db: PgSqlDep):
    user_id = request.state.user_id

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
    user_id = request.state.user_id
    product_inst_part = 'cached'
    if not in_front_cache:
        log_event(Events.bg_product_stage_.format('0' + ' | NO cached'), request, level='WARNING')
        product_inst_part = await db.extended_product.instant_data_product_heavy(prd_id)
    else:    log_event(Events.bg_product_stage_.format('0' + ' | cached!'), request)
    # logging
    task_1lvl_bg = lvl1_render.apply_async(args=[prd_id, in_front_cache, user_id])
    task_2lvl_bg = lvl2_render.apply_async(args=[prd_id, seller_id])
    return {'instantly_data': product_inst_part,
            'task-bg_lvl_1': task_1lvl_bg.id,
            'task-bg_lvl_2': task_2lvl_bg.id, }


@router.get('/bg_lvl3/{prd_id}')
async def run_bg_lvl3(prd_id: int):
    # logging
    task_3lvl_bg = lvl3_render.apply_async(args=[prd_id])
    return {'task-bg_lvl_3': task_3lvl_bg.id}