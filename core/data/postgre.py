from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator
from asyncpg import Connection, create_pool, Pool

from fastapi.params import Depends
from starlette.requests import Request
from typing_extensions import Optional

from core.config_dir.config import pool_settings
from core.data.sql_queries.multi_render_prd_sql import ExtendedProduct
from core.data.sql_queries.products_sql import ProductsQueries
from core.data.sql_queries.users_sql import UsersQueries, AuthQueries
from core.data.sql_queries.chats_sql import ChatQueries


class PgSql:
    def __init__(self, conn: Connection):
        self.conn = conn

        self.users = UsersQueries(conn)
        self.auth = AuthQueries(conn)
        self.chats = ChatQueries(conn)

        self.products = ProductsQueries(conn)
        self.extended_product = ExtendedProduct(conn)


connection: Optional[Pool] = None
async def set_connection():
    global connection
    if connection is None:
        connection = await create_pool(**pool_settings)
    return connection

@asynccontextmanager
async def init_pool():
    pool = await set_connection()
    async with pool.acquire() as session:
        yield PgSql(session)


async def set_session(request: Request) -> AsyncGenerator[Connection, None]:
    async with request.app.state.pg_pool.acquire() as session:
        yield session

async def get_pgsql_dependency(conn: Annotated[Connection, Depends(set_session)]):
    yield PgSql(conn)

PgSqlDep = Annotated[PgSql, Depends(get_pgsql_dependency)]
