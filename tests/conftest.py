import os
import subprocess
import time
from collections.abc import Callable

import pytest
import pytest_asyncio
from asyncpg import create_pool
from httpx import AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config_dir.config import pool_settings, get_uvicorn_host
from core.config_dir.logger import log_event
from core.config_dir.urls_middlewares import allowed_ips, white_list_prefix_NO_COOKIES
from core.utils.anything import Events
from core.utils.ping_test_server import wait_conn
from core.utils.processing_data.ip_taker import get_client_ip



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
    assert os.getenv('MODE') == 'Test'
    global postgres_pool
    if postgres_pool is None:
        log_event('Создаём пул с БД для тестов', level='WARNING')
        postgres_pool = await create_pool(**pool_settings, max_size=30)
    return postgres_pool


class SimpleAuthMiddlewareTest(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        url = request.url.path
        ip = get_client_ip(request)

        "Веб-адреса или запросы Сервера"
        if not url.startswith('/api') or ip in allowed_ips:
            log_event(Events.white_list_url, request=request)
            request.state.user_id = int(request.cookies.get('access_token') or 1)
            request.state.session_id = request.cookies.get('refresh_token') or '1'
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


@pytest.fixture(scope='session')
def uvicorn_test_server():
    assert os.getenv('MODE') == 'Test'
    os.environ['PYTHONUTF8'] = '1'

    host = get_uvicorn_host()
    port = '8000'

    proccess = subprocess.Popen([
        'uvicorn',
        'core.test_main:test_app',
        '--host', host,
        '--port', port
    ])
    wait_conn(host, port)

    yield
    proccess.terminate()
    proccess.wait()

@pytest_asyncio.fixture
async def ac(uvicorn_test_server, prepare_test_db):
    async with AsyncClient(base_url=f'http://{get_uvicorn_host()}:8000') as async_client:
        yield async_client


@pytest_asyncio.fixture(scope='session', autouse=True)
async def prepare_test_db(pg_db):
    setup_queries = [
        """insert into public.users (name, email, passw) values
         ('admin_user', 'test_plug@gmail.com', 'plugpassw'),
         ('test_user1', 'test_user1@gmail.com', 'userpassw1'),
         ('test_user2', 'test_user2@gmail.com', 'userpassw2'),
         ('test_user1', 'test_user3@gmail.com', 'userpassw3'),
         ('test_user2', 'test_user4@gmail.com', 'userpassw4')""",
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

        "insert into chats (is_group) values(false), (false)",
        """insert into chat_users (chat_id, user_id, chat_name) values
         (1, 2, 'test_chat_1-3'), (1, 3, 'test_chat_1-2'),
         (2, 4, 'test_chat_2-5'), (2, 5, 'test_chat_2-4')""",
        """insert into chat_messages (chat_id, owner_id, text_field, type, local_id, is_commited, content_path) values
        (1, 2, 'test mes 1', 2, 1, true, 'users/chats/test_bulk1.png'), (1, 2, 'test mes 2', 2, 2, true, 'users/chats/test_bulk2.png'),(1, 2, 'test mes 3', 1, 3, true, null)""",
        "insert into readed_mes (chat_id, user_id, last_read_local_id) values(1, 2, 3)",
    ]
    async with pg_db.acquire() as conn:
        await conn.execute(f"TRUNCATE TABLE {','.join(db_tables)} RESTART IDENTITY CASCADE")
        for query in setup_queries:
            await conn.execute(query)

@pytest.fixture
def xff_ip():
    return {'X-Forwarded-For': '111.0.111.0, 127.0.0.1'}

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
