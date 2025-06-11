from fastapi import APIRouter

from core.config_dir.base_dependencies import PagenSearchDep
from core.config_dir.config import get_env_vars, es_client
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.schemas.product_schemas import SearchSchema
from core.utils.anything import Tags
from core.utils.searching.elastic_utils import gener_docs
from core.utils.searching.index_settings import index_mapping, aliases, settings
from core.utils.searching.search_ptn import looking

router = APIRouter(prefix='/api/products/elastic', tags=[Tags.elastic_products])
search_index =  get_env_vars().search_index


@router.put('/index_up/{index_name}', summary='Название индекса может быть произвольным, но не должно совпадать с Элиасом')
async def put_index(index_name: str):
    async with es_client as aioes:
        await aioes.indices.create(index=index_name,
                                   aliases=aliases,
                                   settings=settings,
                                   mappings=index_mapping)
    return {'success': True, 'message': f'Индекс {index_name} поднят, прожми бульк-вставку!'}


@router.post('/bulk_docs')
async def add_docs_in_index(
        db: PgSqlDep,
):
    records = await db.products.get_search_docs_BULK()
    async with es_client as aioes:
        async for doc in gener_docs(records):
            action = {'index': {'_index': search_index, '_id': doc['id']}}
            body = {'prd_name': doc['prd_name'], 'category': doc['category']}
            await aioes.bulk(body=[action, body])
    return {'success': True, 'message': 'Чекни эластик!'}


@router.post('/search')
async def search(search_string: SearchSchema, db: PgSqlDep, pagen: PagenSearchDep):
    """
    в будущем подрубить редис, если будет находить < 40 записей, чтобы быстро фильтровать
    """
    async with es_client as aioes:
        search_res = await aioes.search(
            query=looking(search_string.text),
            index=search_index,
            source=False,
            filter_path='hits.hits',
            from_=pagen.offset,
            size=pagen.limit,
        )
    ids_prdts = tuple(int(hit['_id']) for hit in search_res['hits']['hits'])
    log_event("Поисковая выдача: search_string: \"%s\"; length hits: %s", search_string.text, len(ids_prdts), level='WARNING')
    layout_products = await db.products.products_by_id(ids_prdts)
    return {'products': layout_products}