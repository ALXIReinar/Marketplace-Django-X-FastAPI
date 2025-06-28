import os

import pytest

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



"Options from CLI"
def pytest_addoption(parser):
    parser.addoption(
        '--run-mode',
        default='default',
        choices=('default', 'stress')
    )

@pytest.fixture(scope='session')
def run_mode(request):
    return request.config.getoption('--run-mode')
