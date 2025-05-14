from fastapi import APIRouter

from core.config_dir.base_dependencies import PagenDep
from core.config_dir.logger import Tags
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import UserBase

router = APIRouter(prefix='/api/products')



@router.post('/', tags=[Tags.products], summary="Выдать Карточки товаров")
async def preview_products(user: UserBase, pagen: PagenDep, db: PgSqlDep):
     """
     Учесть фактор отсутствия/наличия! авторизации
     """
     records = await db.welcome_page_select(user.id, pagen.offset, pagen.limit)
     return {'products': records.products,
             'counters': [
                  {'favorite': records.favorite}, {'ordered_items': records.ordered_items}]
             }