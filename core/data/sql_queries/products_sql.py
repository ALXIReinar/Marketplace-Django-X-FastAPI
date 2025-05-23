from collections import namedtuple

from asyncpg import Connection


class ProductsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def welcome_page_select(self, user_id, offset, limit):
        query_layout_products = """
        SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, COUNT(c.id_comment), AVG(c.rate)
        FROM products p
        JOIN images_prdts img ON p.id = img.prd_id AND img.position = 1
        LEFT JOIN comments c ON c.prd_id = p.id
        WHERE p.category_id IN (
            SELECT category_id FROM preferences_users 
            WHERE user_id = $1 ORDER BY counter DESC LIMIT 3)
        AND p.remain > 0
        GROUP BY p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path
        OFFSET $2 LIMIT $3"""

        query_counters = """
        SELECT 
            (SELECT COUNT(*) FROM favorite WHERE user_id = $1) AS f_count,
	        (SELECT COUNT(*) FROM ordered_products WHERE status != 'Завершён' AND order_id IN (
		        SELECT "id" FROM orders WHERE user_id = $1)
            ) AS ord_items"""

        layout_products = await self.conn.fetch(query_layout_products, user_id, offset, limit)
        if user_id == 1:
            f_count, ord_count = 0, 0
        else:
            counters = await self.conn.fetchrow(query_counters, user_id)
            f_count, ord_count = counters['f_count'], counters['ord_items']

        named_res = namedtuple('Records', ('products', 'favorite', 'ordered_items'))
        return named_res(layout_products, f_count, ord_count)


    async def get_search_docs_BULK(self):
        query = """
        SELECT p."id", p.prd_name, d_p.category_full FROM products p
        JOIN details_prdts d_p ON p."id" = d_p.prd_id
        GROUP BY p."id", p.prd_name, d_p.category_full
        """
        records = await self.conn.fetch(query)
        return records

    async def products_by_id(self, ids_prdts: tuple):
        query = """
        SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days, COUNT(c.id_comment), AVG(c.rate) FROM products p
        LEFT JOIN comments c ON c.prd_id = p.id
        JOIN images_prdts img ON img.prd_id = p.id AND img.position = 1
        JOIN details_prdts d_p ON d_p.prd_id = p.id 
        WHERE p.id = ANY($1)
        AND p.remain > 0
        GROUP BY p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days
        """
        records = await self.conn.fetch(query, ids_prdts)
        return records