import os

import pytest
from httpx import AsyncClient, ASGITransport

from core.config_dir.config import app, env

'''

FOR ALL FIXTURES!!!(and options)

'''

@pytest.fixture(scope='session')
def setup_db():
    assert os.getenv('MODE','mode') == 'Test'
    # log_event('Создаём БД для тестов', level='WARNING')
    # db.init_db()
    # yield
    # db.flush_db()
    # log_event('БД для тестов Очищена!', level='WARNING')

@pytest.fixture
async def ac():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f'http://{env.uvicorn_host}:8000'
    ) as async_client:
        yield async_client


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
