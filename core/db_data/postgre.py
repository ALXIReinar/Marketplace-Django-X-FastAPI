from collections import namedtuple
from typing import Annotated
from asyncpg import Connection

from fastapi.params import Depends

from core.config_dir.config import set_session

class PgSql:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def welcome_page_select(self, offset, limit, user_id=1):
        """
        учесть, что потом к этому запросу нужно будет прикручивать выборку счётчиков:
        для сообщений чата, заказов, избранное, корзина и т.п
        """
        query_layout_products = """SELECT p.id, p.seller_id, p.prd_name, p.cost, img.path FROM products p
                   JOIN images_prdts img ON p.id = img.prd_id
                   WHERE p.category IN (SELECT category FROM preferences_users WHERE user_id = $1)
                   GROUP BY p.id, p.seller_id, p.prd_name, p.cost, img.path 
                   OFFSET $2 LIMIT $3"""

        query_count_favorite = "SELECT COUNT(f.*) FROM favorite f WHERE user_id = $1"

        query_count_ordered_products = """SELECT COUNT(*) FROM ordered_products
                                          WHERE status != 'Завершён' 
                                          AND order_id IN (SELECT "id" FROM orders WHERE user_id = $1)"""

        layout_products = await self.conn.fetch(query_layout_products, user_id, offset, limit)
        count_favorite = await self.conn.fetchrow(query_count_favorite, user_id)
        count_ordered_products = await self.conn.fetchrow(query_count_ordered_products, user_id)

        named_res = namedtuple('Records', ('products', 'favorite', 'ordered_items'))
        return named_res(layout_products, count_favorite['count'], count_ordered_products['count'])


async def get_pgsql_dependency(conn: Annotated[Connection, Depends(set_session)]):
    yield PgSql(conn)

PgSqlDep = Annotated[Connection, Depends(get_pgsql_dependency)]
