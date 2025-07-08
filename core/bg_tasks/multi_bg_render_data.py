from fastapi import APIRouter
from starlette.requests import Request

from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.schemas.product_schemas import LVL1ExtendedPrdSchema, LVL2ExtendedPrdSchema, ProductBase
from core.utils.anything import Events

router = APIRouter(prefix='/public/bg_tasks/ext_prd')



@router.post('/lvl1')
async def lvl1_load_data(bg_obj: LVL1ExtendedPrdSchema, request: Request, db: PgSqlDep):
    log_event(Events.bg_call_func.format(1) + f"prd_id: %s; front_cached: %s; user_id: %s",
              bg_obj.prd_id, bg_obj.front_cached, bg_obj.user_id, request=request)
    data = await db.extended_product.primary_background(bg_obj.prd_id, bg_obj.front_cached, bg_obj.user_id)
    return data


@router.post('/lvl2')
async def lvl2_load_data(bg_obj: LVL2ExtendedPrdSchema, request: Request, db: PgSqlDep):
    log_event(Events.bg_call_func.format(2) + f"prd_id: {bg_obj.prd_id}; seller_id: {bg_obj.seller_id}", request=request)
    data = await db.extended_product.secondary_background(bg_obj.prd_id, bg_obj.seller_id)
    return data


@router.post('/lvl3')
async def lvl3_load_data(ext_prd: ProductBase, request: Request, db: PgSqlDep):
    log_event(Events.bg_call_func.format(3) + f"prd_id: {ext_prd.prd_id}", request=request)
    data = await db.extended_product.tertiary_background(ext_prd.prd_id)
    return data
