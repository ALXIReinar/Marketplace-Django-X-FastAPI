from contextlib import asynccontextmanager
from typing import Callable

import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.api import main_router
from core.api.middlewares import TrafficCounterMiddleware
from core.bg_tasks import bg_router
from core.config_dir.config import get_host_port_ES, env, get_uvicorn_host
from core.config_dir.logger import log_event
from core.config_dir.urls_middlewares import allowed_ips, white_list_prefix_NO_COOKIES
from core.utils.anything import Events
from core.utils.processing_data.ip_taker import get_client_ip


@asynccontextmanager
async def lifespan(web_app: FastAPI):
    yield

auth_app = FastAPI(lifespan=lifespan)
auth_app.include_router(main_router)
auth_app.include_router(bg_router)

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


ddos_app = FastAPI(lifespan=lifespan)
ddos_app.add_middleware(TrafficCounterMiddleware, requests_limit=env.requests_limit, ttl_limit=env.ttl_requests_limit)

@pytest_asyncio.fixture()
async def ddos_ac():
    async with AsyncClient(
            base_url=f'http://{get_uvicorn_host()}:8100',
            transport=ASGITransport(ddos_app)
    ) as async_client:
        yield async_client

@pytest_asyncio.fixture
async def auth_ac():
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url=f'http://{get_uvicorn_host()}:8100'
    ) as auth_async_client:
        yield auth_async_client

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
async def prepare_elasticsearch(uvicorn_test_server, run_mode):
    if run_mode == 'ci_test':
        aioes = AsyncElasticsearch(**get_host_port_ES())
        await aioes.indices.delete(index='test_index1')
        await aioes.close()
    yield

def get_urls_plan(cookies: bool):
    arr = [
        ('POST', '/api/public/bg_tasks/ext_prd/lvl1', '216.189.251.110, '),
        ('POST', '/api/public/users/sign_up', '142.30.96.2, '),
        ('GET', '/api/docs', '8.57.84.199, '),
        ('GET', '/api/public/bg_tasks/51532', '247.148.22.132, '),
        ('GET', '/api/orders/', '39.106.100.195, '),
        ('GET', '/images/icons8-поиск-24.png', '203.233.188.197, '),
        ('POST', '/api/chats/send_file/s3', '159.236.185.140, '),
        ('POST', '/api/chats/bulk_presigned_urls', '189.155.142.52, '),
        ('POST', '/api/public/bg_tasks/ext_prd/lvl3', '177.147.229.108, '),
        ('DELETE', '/api/server/crons/flush_refresh-tokens', '235.63.51.139, '),
        ('POST', '/api/users/profile/seances', '61.249.72.110, '),
        ('PUT', '/api/server/crons/s3_fs-manager', '46.107.48.241, '),
        ('POST', '/api/chats/send_message', '221.65.233.150, '),
        ('POST', '/api/chats/get_file/local', '59.66.50.226, '),
        ('GET', '/api/public/users/passw/compare_confirm_code?reset_token=123&code=123', '205.15.94.205, '),
        ('PUT', '/api/public/users/passw/set_new_passw', '160.200.163.29, '),
        ('POST', '/api/products/elastic/search?limit=40&offset=0', '214.220.95.226, '),
        ('PUT', '/api/private/bg_tasks/s3_upload/saving?file_path=2', '136.86.163.26, '),
        ('POST', '/api/public/users/login', '141.218.122.85, '),
        ('GET', '/.well-known/appspecific/com.chrome.devtools.json', '46.169.168.157, '),
        ('POST', '/api/products/?limit=60&offset=0', '62.3.107.68, '),
        ('GET', '/favicon.ico', '188.198.144.238, '),
        ('GET', '/api/openapi.json', '151.187.55.19, '),
        ('GET', '/api/orders/purchased?limit=40&offset=0', '103.142.183.40, '),
        ('POST', '/api/chats/send_file/local', '253.155.252.167, '),
        ('POST', '/api/public/users/passw/forget_passw', '212.119.196.15, '),
        ('GET', '/api/orders/sections?status=true&limit=60&offset=0', '201.156.245.219, '),
        ('PUT', '/api/chats/set_readed', '87.71.106.153, '),
        ('GET', '/index.css', '64.134.184.204, '),
        ('GET', '/api/chats/get_ws_token', '57.227.52.217, '),
        ('PUT', '/api/elastic/index_up/344', '79.63.254.173, '),
        ('POST', '/api/public/bg_tasks/email_check', '22.74.35.12, '),
        ('GET', '/', '15.17.43.60, '),
        ('GET', '/api/products/77_3?in_front_cache=false', '235.184.231.125, '),
        ('POST', '/api/public/bg_tasks/ext_prd/lvl2', '197.167.14.250, '),
        ('DELETE', '/api/server/crons/delete_chat-messages', '98.9.78.203, '),
        ('GET', '/api/favorites/?limit=20&offset=0', '227.231.82.57, '),
        ('PUT', '/api/chats/commit_msg', '88.64.253.76, '),
        ('GET', '/api/chats/?limit=30&offset=0', '140.44.124.50, '),
        ('POST', '/api/private/users/logout', '135.237.117.174, ')
    ]
    status_codes_cookies = (
        (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (401, 1), (200, 2), (200, 2), (200, 2),
        (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (401, 1), (200, 2), (200, 2), (200, 2), (200, 2),
        (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (401, 1), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2),
        (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2), (200, 2)
    )
    status_codes_wo_cookies = (
        200, 200, 401, 200, 200, 200, 401, 401, 200, 401, 401, 401, 401, 401, 200, 200, 200, 401, 200, 200, 200, 200,
        401, 200, 401, 200, 200, 401, 200, 401, 401, 200, 200, 200, 200, 401, 200, 401, 401, 401, 401
    )
    if cookies:
        res = [(meth, endpoint, ip, status_codes_cookies[idx][0], status_codes_cookies[idx][1]) for idx, (meth, endpoint, ip) in enumerate(arr)]
    else:
        res = [(meth, endpoint, ip, status_codes_wo_cookies[idx]) for idx, (meth, endpoint, ip) in enumerate(arr)]

    # random_ip = []
    # for i in range(len(arr)):
    #     ip_quarts = tuple(str(randint(0, 255)) for _ in range(4))
    #     ip = '.'.join(ip_quarts) + ', '
    #     random_ip.append(ip)
    return res
