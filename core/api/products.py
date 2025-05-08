from fastapi import APIRouter

from core.config_dir.base_dependencies import PagenDep
from core.db_data.postgre import PgSqlDep

router = APIRouter()



@router.get('/')
async def preview_products(pagen: PagenDep, db: PgSqlDep):
     """
     Учесть фактор отсутствия/наличия! авторизации
     Брать id из куки
     """
     records = await db.welcome_page_select(pagen.offset, pagen.limit)
     return {'products': records.products,
             'counters': [
                  {'favorite': records.favorite}, {'ordered_items': records.ordered_items}]
             }