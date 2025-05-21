from fastapi import APIRouter, Request

from core.data.postgre import PgSqlDep
from core.config_dir.base_dependencies import PagenDep
from core.config_dir.config import get_env_vars, es_client
from core.utils.searching.elastic_utils import gener_docs
from core.utils.anything import Tags

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


"""
ElasticSearch Эндпоинты
"""

@router.post('/elastic/bulk_docs', tags=[Tags.elastic_products])
async def add_docs_in_index(
        db: PgSqlDep,
):
    records = await db.products.get_search_docs_BULK()
    async with es_client as aioes:
        async for doc in gener_docs(records):
            action = {'index': {'_index': get_env_vars().search_index, '_id': doc['id']}}
            body = {'prd_name': doc['prd_name'], 'category': doc['category']}
            await aioes.bulk(body=[action, body])
    return {'success': True, 'message': 'Чекни эластик!'}
