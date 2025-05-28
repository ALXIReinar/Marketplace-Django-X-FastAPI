from contextlib import asynccontextmanager
from typing import Annotated
from asyncpg import Connection, create_pool

from fastapi.params import Depends

from core.config_dir.config import set_session, pool_settings
from core.data.sql_queries.multi_render_prd_sql import ExtendedProduct
from core.data.sql_queries.products_sql import ProductsQueries
from core.data.sql_queries.users_sql import UsersQueries, AuthQueries


class PgSql:
    def __init__(self, conn: Connection):
        self.conn = conn

        self.users = UsersQueries(conn)
        self.auth = AuthQueries(conn)

        self.products = ProductsQueries(conn)
        self.extended_product = ExtendedProduct(conn)

@asynccontextmanager
async def init_pool():
    connection = await create_pool(**pool_settings)
    async with connection.acquire() as session:
        yield PgSql(session)

async def get_pgsql_dependency(conn: Annotated[Connection, Depends(set_session)]):
    yield PgSql(conn)

PgSqlDep = Annotated[PgSql, Depends(get_pgsql_dependency)]
