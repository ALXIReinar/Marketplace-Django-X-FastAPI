import asyncio

from core.bg_tasks.multi_bg_render_data import lvl1_load_data, lvl2_load_data, lvl3_load_data
from core.config_dir.celery_config import celery_bg, ext_prd_queue, large_prd_routing_key


@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl1_render(prd_id: int, front_cached: bool, user_id: int):
    # log_debug(Events.bg_product_stage_.format(1) + f' | prd_id = {prd_id}', level='INFO')
    return asyncio.run(lvl1_load_data(prd_id, front_cached, user_id))


@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl2_render(prd_id: int, seller_id: int):
    # logging
    return asyncio.run(lvl2_load_data(prd_id, seller_id))


@celery_bg.task(queue=ext_prd_queue, routing_key=large_prd_routing_key)
def lvl3_render(prd_id: int):
    # logging
    return asyncio.run(lvl3_load_data(prd_id))