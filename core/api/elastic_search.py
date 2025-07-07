from elasticsearch import NotFoundError
from fastapi import APIRouter

from core.config_dir.base_dependencies import PagenSearchDep, ElasticDep
from core.config_dir.config import env
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.schemas.product_schemas import SearchSchema
from core.utils.anything import Tags
from core.utils.searching.index_settings import index_mapping, aliases, settings
from core.utils.searching.search_ptn import looking

router = APIRouter(tags=[Tags.elastic_products])
search_index = env.search_index


@router.put('/api/elastic/index_up/{index_name}', summary='Название индекса может быть произвольным, но не должно совпадать с Элиасом')
async def put_index(index_name: str, db: PgSqlDep, es_client: ElasticDep):
    records = await db.products.get_search_docs_BULK()
    async with es_client as aioes:
        "Обеспечение Идемпотентности ручки"
        try:
            aliases_ = await aioes.indices.get_alias(name=search_index)
            if aliases_:
                return {'success': False, 'message': "Индекс уже был создан и Проиндексирован"}
        except NotFoundError:
            pass

        "Создаём и Наполняем индекс"
        await aioes.indices.create(index=index_name,
                                   aliases=aliases,
                                   settings=settings,
                                   mappings=index_mapping)
        batch = []
        for record in records:
            category = ''.join(record['category_full'].replace('/', ' '))
            doc = {
                "id": record['id'],
                "prd_name": record['prd_name'],
                "category": category
            }
            batch.append({'index': {'_index': index_name, '_id': doc['id']}})       # action
            batch.append({'prd_name': doc['prd_name'], 'category': doc['category']})  # body
            if len(batch) >= 2000:
                await aioes.bulk(body=batch)
                batch.clear()
        if batch:
            await aioes.bulk(body=batch, refresh=True)
        else:    await aioes.indices.refresh(index=index_name)

        return {'success': True, 'message': f'Индекс {index_name} поднят, документы вставлены'}


@router.post('/api/products/elastic/search')
async def search(search_string: SearchSchema, pagen: PagenSearchDep, db: PgSqlDep, es_client: ElasticDep):
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
    log_event(f'{search_res}', level='DEBUG')
    ids_prdts = tuple(int(hit['_id']) for hit in search_res['hits']['hits'])
    log_event("Поисковая выдача: search_string: \"%s\"; length hits: %s", search_string.text, len(ids_prdts), level='WARNING')
    layout_products = await db.products.products_by_id(ids_prdts)
    return {'products': layout_products}