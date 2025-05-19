from collections import namedtuple

from asyncpg import Connection


class ProductsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def welcome_page_select(self, user_id, offset, limit):
        query_layout_products = """SELECT p.id, p.seller_id, p.prd_name, p.cost, img.path FROM products p
                   JOIN images_prdts img ON p.id = img.prd_id
                   WHERE p.category IN (
                       SELECT category FROM preferences_users WHERE user_id = $1
                       ORDER BY counter DESC LIMIT 3)
                   GROUP BY p.id, p.seller_id, p.prd_name, p.cost, img.path 
                   OFFSET $2 LIMIT $3"""

        query_count_favorite = "SELECT COUNT(*) FROM favorite WHERE user_id = $1"

        query_count_ordered_products = """SELECT COUNT(*) FROM ordered_products
                                          WHERE status != 'Завершён' 
                                          AND order_id IN (SELECT "id" FROM orders WHERE user_id = $1)"""

        layout_products = await self.conn.fetch(query_layout_products, user_id, offset, limit)
        if user_id == 1:
            f_count = 0
            ord_count = 0
        else:
            f_count = (await self.conn.fetchrow(query_count_favorite, user_id))['count']
            ord_count = (await self.conn.fetchrow(query_count_ordered_products, user_id))['count']

        named_res = namedtuple('Records', ('products', 'favorite', 'ordered_items'))
        return named_res(layout_products, f_count, ord_count)