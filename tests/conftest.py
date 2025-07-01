import os
from collections.abc import Callable

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request

from core.api import main_router
from core.bg_tasks import bg_router
from core.config_dir.config import app, env


app.user_middleware.clear()

@app.middleware('http')
async def auth_ux_test_middleware(request: Request, call_next: Callable):
    ...
    return await call_next(request)

app.include_router(main_router)
app.include_router(bg_router)


@pytest_asyncio.fixture
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f'http://{env.uvicorn_host}:8000'
    ) as async_client:
        yield async_client

@pytest.fixture(scope='session')
def setup_db():
    assert os.getenv('MODE','mode') == 'Test'
    # log_event('Создаём БД для тестов', level='WARNING')
    # db.init_db()
    # yield
    # db.flush_db()
    # log_event('БД для тестов Очищена!', level='WARNING')



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
