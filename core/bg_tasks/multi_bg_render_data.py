from core.config_dir.debug_logger import log_debug
from core.data.postgre import init_pool
from core.utils.anything import Events


async def lvl1_load_data(prd_id: int, front_cached: bool):
    # log_debug(Events.bg_product_stage_.format(1))
    async with init_pool() as db:
        data = await db.extended_product.primary_background(prd_id, front_cached)
    return data