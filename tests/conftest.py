import os
from collections.abc import Callable

import pytest
import pytest_asyncio
from asyncpg import create_pool
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.api import main_router
from core.bg_tasks import bg_router
from core.config_dir.config import env, pool_settings
from core.config_dir.logger import log_event
from core.config_dir.urls_middlewares import allowed_ips, white_list_prefix_NO_COOKIES
from core.utils.anything import Events
from core.utils.processing_data.ip_taker import get_client_ip

app = FastAPI()
auth_app = FastAPI()

db_tables = [
    'addresses_prd_points',
    'addresses_users',
    'categories',
    'chat_messages',
    'chat_users',
    'chats',
    'comments',
    'details_prdts',
    'favorite',
    'images_prdts',
    'media_comments',
    'ordered_products',
    'orders',
    'prd_headers',
    'prd_stats',
    'prd_subheaders',
    'preferences_users',
    'products',
    'readed_mes',
    'sellers',
    'sessions_users',
    'shop_cart',
    'users',
]

postgres_pool = None
@pytest_asyncio.fixture(scope='session', autouse=True)
async def pg_db():
    assert os.getenv('MODE', 'mode') == 'Test'

    global postgres_pool
    if postgres_pool is None:
        log_event('Создаём пул с БД для тестов', level='WARNING')
        postgres_pool = await create_pool(**pool_settings, max_size=30)
    return postgres_pool


@auth_app.middleware('http')
async def auth_ux_test_middleware(request: Request, call_next: Callable):
    url = request.url.path
    ip = get_client_ip(request)

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

auth_app.include_router(bg_router)
auth_app.include_router(bg_router)

@pytest_asyncio.fixture
async def auth_ac():
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url=f'http://{env.uvicorn_host}:8000'
    ) as auth_async_client:
        yield auth_async_client


@app.middleware('http')
async def integrate_test_auth_middleware(request: Request, call_next: Callable):
    url = request.url.path
    ip = get_client_ip(request)

    "Веб-адреса или запросы Сервера"
    if not url.startswith('/api') or ip in allowed_ips:
        log_event(Events.white_list_url, request=request)
        return await call_next(request)
    "Не нуждаются в авторизации, Если нет кук"
    if not request.cookies and any(tuple(url.startswith(prefix) for prefix in white_list_prefix_NO_COOKIES)):
        log_event(Events.white_list_url, request=request, level='WARNING')
        return await call_next(request)
    "Только если есть aT и rT"
    aT, rT = request.cookies.get('access_token'), request.cookies.get('refresh_token')
    if aT and rT:
        request.state.user_id = int(aT)
        request.state.session_id = rT
        return await call_next(request)
    return JSONResponse(status_code=401, content={'message': 'UnAuthorized'})


@pytest_asyncio.fixture(scope='session')
async def app_with_db(pg_db):
    app.state.pg_pool = pg_db
    yield app

@pytest_asyncio.fixture
async def ac(app_with_db):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_db),
        base_url=f'http://{env.uvicorn_host}:8000'
    ) as async_client:
        yield async_client

@pytest_asyncio.fixture
async def auth_ac_methods(auth_ac):
    ac_methods = {
        'POST': auth_ac.post,
        'GET': auth_ac.get,
        'DELETE': auth_ac.delete,
        'PUT': auth_ac.put
    }
    return ac_methods


@pytest_asyncio.fixture(scope='session', autouse=True)
async def prepare_user_seller_product(pg_db):
    setup_queries = [
        "insert into public.users (name, email, passw) values ('admin_user', 'test_plug@gmail.com', 'plugpassw'),('test_user1', 'test_user1@gmail.com', 'userpassw'), ('test_user2', 'test_user2@gmail.com', 'userpassw')",
        "insert into addresses_prd_points (address_text, work_time_start, work_time_end) values ('Небылинск, ул. Колотушкина,  д.44', '09:00.00', '21:00.00')",
        "insert into addresses_users (user_id, prd_point_id) values(2, 1), (3, 1)",

        "insert into sellers (title_shop, email, passw) values('test_shop', 'test_seller@gmail.com', 'sellerpassw')",
        "insert into categories (designation) values('Электроника'), ('Одежда')",

        "insert into products (seller_id, category_id, prd_name, cost, remain) values(1,1, 'test pc1', 100, 1), (1,1, 'test pc2', 200, 1), (1,2, 'test clothe1', 300, 1), (1,2, 'test clothe2', 400, 0)",
        """insert into images_prdts (prd_id, path, position, title_img) 
        values (1, '/images/products/1_1.png', 1, false), (1, '/images/products/1_2.png', 2, true), (1, '/images/products/1_3.png', 3, false), 
        (2, '/images/products/2_1.png', 1, true), (2, '/images/products/2_2.png', 2, false), (2, '/images/products/1_3.png', 3, false),
        (3, '/images/products/3_1.png', 1, false), (3, '/images/products/3_2.png', 2, true), 
        (4, '/images/products/4_1.png', 1, true), (4, '/images/products/4_2.png', 2, false)
        """,
        """insert into public.details_prdts (prd_id, descr_md, category_full, delivery_days, articul) values
         (1,'/descr_md/1.md','тест_электроника/компьютеры и периферия/ноутбуки', 1, 1),
         (2,'/descr_md/2.md','тест_электроника/компьютеры и периферия/ноутбуки', 2, 2),
         (3,'/descr_md/3.md','тест_электроника/компьютеры и периферия/ноутбуки', 3, 3),
         (4,'/descr_md/4.md','тест_электроника/компьютеры и периферия', 4,4)""",

        "insert into orders (user_id, total_cost, address_id, status) values(2, 300, 1, 'Завершённые'), (3, 600, 1, 'Актуальные')",
        """insert into ordered_products (order_id, prd_id, fixed_cost, qty, delivery_date_start, delivery_date_end, delivery_company, track_num, prd_status)
         values (1, 1, 100, 1, '2025-05-05','2025-06-20', 'aboba delivery', 'XY1', 'Получен'), (1, 3, 300, 1, '2025-05-05','2025-06-20', 'pego delivery', 'XZ2', 'Получен'),
          (2, 2, 200, 1, '2025-05-05','2025-06-20', 'pego delivery', 'XC3', 'Собираем заказ'), (2, 4, 400, 1, '2025-05-05','2025-06-20', 'aboba delivery', 'XA4', 'Получен')""",

        "insert into favorite (user_id, prd_id) values(2, 1), (2, 2), (2, 3), (2, 4)",
        "insert into preferences_users (user_id, category_id) values(2, 1), (2, 2), (3, 1)",

    ]
    async with pg_db.acquire() as conn:
        await conn.execute(f"TRUNCATE TABLE {','.join(db_tables)} RESTART IDENTITY CASCADE")
        for query in setup_queries:
            await conn.execute(query)

@pytest.fixture
def xff_ip():
    return {'X-Forwarded-For': '111.0.111.0, '}

"Options from CLI"
def pytest_addoption(parser):
    parser.addoption(
        '--run-mode',
        default='default',
        choices=('default', 'stress', 'elastic')
    )

@pytest.fixture(scope='session', autouse=True)
def run_mode(request):
    return request.config.getoption('--run-mode')
