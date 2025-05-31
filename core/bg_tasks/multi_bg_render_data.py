from core.config_dir.debug_logger import log_debug
from core.data.postgre import init_pool
from core.utils.anything import Events


async def lvl1_load_data(prd_id: int, front_cached: bool, user_id: int):
    # log_debug(Events.bg_product_stage_.format(1))
    async with init_pool() as db:
        data = await db.extended_product.primary_background(prd_id, front_cached, user_id)
    return data

async def lvl2_load_data(prd_id: int, seller_id: int):
    # Логинг
    async with init_pool() as db:
        data = await db.extended_product.secondary_background(prd_id, seller_id)
    return data

async def lvl3_load_data(prd_id: int):
    # Логинг!
    async with init_pool() as db:
        data = await db.extended_product.tertiary_background(prd_id)
    return data