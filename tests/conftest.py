import os
from collections.abc import Callable

import pytest
import pytest_asyncio
from asyncpg import create_pool
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.api import main_router
from core.bg_tasks import bg_router
from core.config_dir.config import app, env, pool_settings
from core.config_dir.logger import log_event
from core.config_dir.urls_middlewares import trusted_proxies, allowed_ips, white_list_prefix_NO_COOKIES
from core.data.postgre import PgSql
from core.utils.anything import Events

app.user_middleware.clear()

@app.middleware('http')
async def auth_ux_test_middleware(request: Request, call_next: Callable):
    url = request.url.path
    xff = request.headers.get('X-Forwarded-For')
    ip = xff.split(',')[0].strip() if (
            xff and request.client.host in trusted_proxies
    ) else request.client.host

    "Веб-адреса или запросы Сервера"
    if not url.startswith('/api') or ip in allowed_ips:
        log_event(Events.white_list_url, request=request)
        return JSONResponse(status_code=200, content={'message': 'вайт лист'})
    "Не нуждаются в авторизации, Если нет кук"
    if not request.cookies and any(tuple(url.startswith(prefix) for prefix in white_list_prefix_NO_COOKIES)):
        log_event(Events.white_list_url, request=request, level='WARNING')
        return JSONResponse(status_code=200, content={'message': 'вайт лист'})
    "Только если есть aT и rT"
    if request.cookies.get('access_token') and request.cookies.get('refresh_token'):
        return JSONResponse(status_code=200, content={'message': 'Процесс подтверждения авторизации'})

    return JSONResponse(status_code=401, content={'message': 'Нужна авторизация'})

app.include_router(main_router)
app.include_router(bg_router)


@pytest_asyncio.fixture
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f'http://{env.uvicorn_host}:8000'
    ) as async_client:
        yield async_client

@pytest_asyncio.fixture
async def ac_methods(ac):
    ac_methods = {
        'POST': ac.post,
        'GET': ac.get,
        'DELETE': ac.delete,
        'PUT': ac.put
    }
    return ac_methods


postgres_pool = None
@pytest_asyncio.fixture(scope='session')
async def pg_pool():
    assert os.getenv('MODE','mode') == 'Test'

    global postgres_pool
    if postgres_pool is None:
        log_event('Создаём пул с БД для тестов', level='WARNING')
        postgres_pool = await create_pool(**pool_settings)
    return postgres_pool

@pytest_asyncio.fixture
async def db_conn(pg_pool):
    async with pg_pool.acquire() as conn:
        async with conn.transaction():
            yield PgSql(conn)


"Options from CLI"
def pytest_addoption(parser):
    parser.addoption(
        '--run-mode',
        default='default',
        choices=('default', 'stress')
    )

@pytest.fixture(scope='session', autouse=True)
def run_mode(request):
    return request.config.getoption('--run-mode')
