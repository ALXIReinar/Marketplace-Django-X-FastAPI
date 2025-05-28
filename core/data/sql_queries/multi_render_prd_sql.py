from asyncpg import Connection


class ExtendedProduct:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def instant_data_product_heavy(self, prd_id: int):
        query_lite_card_data = '''
        SELECT p.prd_name, p.cost, p.remain, COUNT(c.id_comment) AS count_coms, AVG(c.rate) AS avg_rate FROM products p
        LEFT JOIN comments c ON c.prd_id = p.id
        WHERE p.id = $1
        GROUP BY p.prd_name, p.cost, p.remain'''
        query_imgs = 'SELECT path, position FROM images_prdts WHERE prd_id = $1'

        product_info = await self.conn.fetchrow(query_lite_card_data, prd_id)
        images = await self.conn.fetch(query_imgs, prd_id)
        return {
            'product': product_info,
            'images': images
        }

    async def primary_background(self, prd_id: int, lite_mode: bool=True):
        """
        lite_mode: lite/heavy => True/False
        """
        query_prd_img = 'SELECT path, position FROM images_prdts WHERE prd_id = $1 AND position BETWEEN 2 AND 10'
        query_2nd_bg_lay = '''
        SELECT d_p.articul, d_p.category_full, d_p.delivery_days, s.title_shop FROM details_prdts d_p
        JOIN products p ON p.id = d_p.prd_id
        JOIN sellers s ON s.id = p.seller_id
        WHERE p.id = $1
        '''

        data = await self.conn.fetchrow(query_2nd_bg_lay, prd_id)
        prd_images = [] if not lite_mode else await self.conn.fetch(query_prd_img, prd_id)

        records = {
            'product': {
                'articul': data['articul'],
                'delivery_days': data['delivery_days'],
                'bread_crumbs': {
                    'category_full': data['category_full'],
                    'title_shop': data['title_shop']
                }
            },
            'images': prd_images
        }
        return records