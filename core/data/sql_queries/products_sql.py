from collections import namedtuple

from asyncpg import Connection

from core.config_dir.logger import log_event
from core.utils.anything import copy_query_PRODUCTS_BY_ID


class ProductsQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def welcome_page_select(self, user_id, offset, limit):
        query_layout_products = """
        SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, COUNT(c.id) AS count_coms, AVG(c.rate) AS avg_rate
        FROM products p
        JOIN images_prdts img ON p.id = img.prd_id AND img.title_img = true
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
	        (SELECT COUNT(o_p.prd_id) FROM orders o 
            JOIN ordered_products o_p ON o_p.order_id = o.id AND o.status = 'Актуальные'
            WHERE user_id = $1) AS ord_items"""

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
        SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days, COUNT(c.id) AS count_coms, ROUND(AVG(c.rate), 1) AS avg_rate FROM products p
        LEFT JOIN comments c ON c.prd_id = p.id
        JOIN images_prdts img ON img.prd_id = p.id AND img.title_img = true
        JOIN details_prdts d_p ON d_p.prd_id = p.id 
        WHERE p.id = ANY($1)
        AND p.remain > 0
        GROUP BY p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days
        """
        records = await self.conn.fetch(query, ids_prdts)
        return records


    async def favorite_product_list(self, user_id: int, limit: int, offset: int):
        query = '''
        SELECT p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days, COUNT(c.id) AS count_coms, AVG(c.rate) AS avg_rate FROM favorite f
        JOIN products p ON p.id = f.prd_id
        JOIN images_prdts img ON img.prd_id = p.id AND img.title_img = true
        JOIN details_prdts d_p ON d_p.prd_id = p.id
        LEFT JOIN comments c ON c.prd_id = p.id
        WHERE f.user_id = $1
        GROUP BY p.id, p.seller_id, p.prd_name, p.cost, p.remain, img.path, d_p.delivery_days
        LIMIT $2 OFFSET $3
        '''
        res = await self.conn.fetch(query, user_id, limit, offset)
        return res


    async def orders_counters(self, user_id: int):
        query = '''
        SELECT
            (SELECT COUNT(o_p.prd_id) FROM orders o 
            JOIN ordered_products o_p ON o_p.order_id = o.id AND o.status = 'Актуальные'
            WHERE user_id = $1) AS actual_count,
            (SELECT COUNT(o_p.prd_id) FROM orders o 
            JOIN ordered_products o_p ON o_p.order_id = o.id AND o.status = 'Завершённые'
            WHERE user_id = $1) AS complete_count,
            (SELECT COUNT(DISTINCT o_p.prd_id) FROM orders o
            JOIN ordered_products o_p ON o_p.order_id = o.id
            WHERE o_p.prd_status = 'Получен' AND o.user_id = $1) AS purchase_count
        '''
        res = await self.conn.fetchrow(query, user_id)
        return res

    async def orders_product_list(
            self,
            user_id: int,
            status: bool,
            limit: int,
            offset: int
    ):
        order_statuses = {False: "Завершённые", True: "Актуальные"}
        query = '''
        SELECT o.id, o.created_at, o_p.prd_id, o_p.fixed_cost, o_p.prd_status, o_p.delivery_date_end, img.path, COUNT(c.id) FROM orders o
        JOIN ordered_products o_p ON o_p.order_id = o.id
        LEFT JOIN comments c ON c.prd_id = o_p.prd_id
        JOIN images_prdts img ON img.prd_id = o_p.prd_id AND img.title_img = true
        WHERE o.user_id = $1 AND o.status = $2
        GROUP BY o.id, o.created_at, o_p.prd_id, o_p.fixed_cost, o_p.prd_status, o_p.delivery_date_end, img.path
        LIMIT $3 OFFSET $4
        '''
        res = await self.conn.fetch(query, user_id, order_statuses[status], limit, offset)
        return res

    async def purchased_prds(self, user_id: int, limit: int, offset: int):
        query = '''
        SELECT DISTINCT o_p.prd_id FROM orders o
        JOIN ordered_products o_p ON o_p.order_id = o.id
        WHERE o_p.prd_status = 'Получен' AND o.user_id = $1
        LIMIT $2 OFFSET $3
        '''
        products = await self.conn.fetch(copy_query_PRODUCTS_BY_ID.format(query), user_id, limit, offset)
        return products