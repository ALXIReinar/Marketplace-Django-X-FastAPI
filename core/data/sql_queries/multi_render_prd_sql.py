from asyncpg import Connection


class ExtendedProduct:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def instant_data_product_heavy(self, prd_id: int):
        query_lite_card_data = '''
        SELECT p.prd_name, p.cost, p.remain, COUNT(c.id) AS count_coms, AVG(c.rate) AS avg_rate FROM products p
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

    async def primary_background(self, prd_id: int, lite_mode: bool=True, user_id: int=1):
        """
        lite_mode: lite/heavy => True/False
        Добавить выгрузку: 5 главных свойств товара(отд запара для дата-аналитика, по сути)
        """
        query_prd_img = 'SELECT path, position FROM images_prdts WHERE prd_id = $1 AND title_img != true'
        query_bg_lay = '''
        SELECT d_p.articul, d_p.descr_md, d_p.category_full, d_p.delivery_days, s.title_shop FROM details_prdts d_p
        JOIN products p ON p.id = d_p.prd_id
        JOIN sellers s ON s.id = p.seller_id
        WHERE p.id = $1
        '''
        query_address_list = '''
        SELECT a_ps.address_text, a_ps_u.current FROM addresses_prd_points a_ps
        JOIN addresses_users a_ps_u ON a_ps_u.prd_point_id = a_ps.id
        WHERE user_id = $1
        '''
        data = await self.conn.fetchrow(query_bg_lay, prd_id)
        prd_images = [] if not lite_mode else await self.conn.fetch(query_prd_img, prd_id)
        user_address_list = [] if user_id == 1 else await self.conn.fetch(query_address_list, user_id)

        records = {
            'user_data': user_address_list,
            'product': {
                'articul': data['articul'],
                'descr_md': data['descr_md'],
                'delivery_days': data['delivery_days'],
                'bread_crumbs': {
                    'category_full': data['category_full'],
                    'title_shop': data['title_shop']
                }
            },
            'images': prd_images
        }
        return records


    async def secondary_background(self, prd_id: int, seller_id: int):
        query_comments_media = '''
        SELECT m_c.path FROM media_comments m_c
        LEFT JOIN comments c ON m_c.comment_id = c.id
        WHERE c.prd_id = $1
        LIMIT 6'''
        query_avg_rate_by_seller = '''
        SELECT ROUND(AVG(c.rate), 1) AS seller_avg FROM sellers s
        JOIN products p ON p.seller_id = s.id 
        JOIN comments c ON c.prd_id = p.id
        WHERE p.seller_id = $1'''
        query_media_count = '''
        SELECT COUNT(m_c.id) AS media_count from media_comments m_c
        JOIN comments c ON c.id = m_c.comment_id
        WHERE c.prd_id = $1'''

        comments_media_part = await self.conn.fetch(query_comments_media, prd_id)
        avg_seller_prds = await self.conn.fetchrow(query_avg_rate_by_seller, seller_id)
        media_count = await self.conn.fetchrow(query_media_count, prd_id)
        records = {
            'comments_media_preview': comments_media_part,
            'media_count': media_count,
            'seller_avg': avg_seller_prds
        }
        return records


    async def tertiary_background(self, prd_id):
        """
        Запросы
        ----------
        Получаем заголовки
        Выбираем Head_Ids
        ----------
        Получаем подзаголовки
        Достаём SubHead_Ids
        ----------
        Получаем сами параметры
        """
        query_headers = 'SELECT id, title, position FROM prd_headers WHERE prd_id = $1'
        query_subheads = 'SELECT * FROM prd_subheaders WHERE head_id = ANY($1)'
        query_attr_rows = 'SELECT * FROM prd_stats WHERE subhead_id = ANY($1)'

        headers = await self.conn.fetch(query_headers, prd_id)
        head_ids = tuple(record['id'] for record in headers)

        subheaders = await self.conn.fetch(query_subheads, head_ids)
        subhead_ids = tuple(record['head_id'] for record in subheaders)

        stats_rows = await self.conn.fetch(query_attr_rows, subhead_ids)

        return {
            'headers': headers,
            'subheaders': subheaders,
            'stats_rows': stats_rows
        }
