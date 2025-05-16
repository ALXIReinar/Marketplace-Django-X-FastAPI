from collections import namedtuple
from typing import Annotated
from asyncpg import Connection

from fastapi.params import Depends

from core.config_dir.config import set_session, encryption


class PgSql:
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


    async def reg_user(self, email, passw: str, name: str):
        query = 'INSERT INTO users (email, passw, name) VALUES($1, $2, $3) ON CONFLICT (email) DO NOTHING RETURNING id'
        hashed = encryption.hash(passw)

        res = await self.conn.execute(query, email, hashed, name)
        return res


    async def select_user(self, email):
        query = 'SELECT id, passw FROM users WHERE email = $1'
        res = await self.conn.fetchrow(query, email)
        return res


    async def make_session(
            self,
            session_id: str,
            user_id: int,
            iat: int,
            exp: int,
            user_agent: str,
            ip: str,
            hashed_rT: str
    ):
        query = 'INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES($1,$2,$3,$4,$5,$6,$7)'
        await self.conn.execute(query, session_id, user_id, iat, exp, hashed_rT, user_agent, ip)


    async def get_actual_rt(self, user_id: int, session_id: str):
        query = '''SELECT refresh_token, seance FROM sessions_users
                   WHERE user_id = $1 AND session_id = $2 AND "exp" > now()'''
        res = await self.conn.fetchrow(query, user_id, session_id)
        return res

    async def all_seances_user(self, user_id: int, session_id: str):
        query = 'SELECT user_agent, ip FROM sessions_users WHERE user_id = $1 AND session_id = $2'
        res = await self.conn.fetch(query, user_id, session_id)
        return res


async def get_pgsql_dependency(conn: Annotated[Connection, Depends(set_session)]):
    yield PgSql(conn)

PgSqlDep = Annotated[Connection, Depends(get_pgsql_dependency)]
