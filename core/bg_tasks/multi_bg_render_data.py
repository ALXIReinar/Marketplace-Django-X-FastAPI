from core.config_dir.logger import log_event
from core.data.postgre import init_pool
from core.utils.anything import Events


async def lvl1_load_data(prd_id: int, front_cached: bool, user_id: int):
    log_event(Events.bg_call_func.format(1) + f"prd_id: {prd_id}; front_cached: {front_cached}; user_id: {user_id}")
    async with init_pool() as db:
        data = await db.extended_product.primary_background(prd_id, front_cached, user_id)
    return data

async def lvl2_load_data(prd_id: int, seller_id: int):
    log_event(Events.bg_call_func.format(2) + f"prd_id: {prd_id}; seller_id: {seller_id}")
    async with init_pool() as db:
        data = await db.extended_product.secondary_background(prd_id, seller_id)
    return data

async def lvl3_load_data(prd_id: int):
    log_event(Events.bg_call_func.format(3) + f"prd_id: {prd_id}")
    async with init_pool() as db:
        data = await db.extended_product.tertiary_background(prd_id)
    return data