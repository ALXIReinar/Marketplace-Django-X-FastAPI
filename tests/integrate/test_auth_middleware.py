import pytest

from core.config_dir.logger import log_event
from core.utils.processing_data.log_parser import get_actual_endpoint_set
from tests.integrate.conftest import get_urls_plan


@pytest.mark.parametrize(
    'method, endpoint, ip',
    get_urls_plan()
)
@pytest.mark.asyncio
async def test_auth_control_wo(ac, method, endpoint, ip):
    request_meth = {
        'POST': ac.post,
        'GET': ac.get,
        'DELETE': ac.delete,
        'PUT': ac.put
    }
    res = await request_meth[method](endpoint, headers={'X-Forwarded-For': ip})
    log_event(f'{res}', level='DEBUG')


@pytest.mark.skipif('config.getoption("--run-mode") == "default"')
def test_fixture():
    get_urls_plan()
    assert 1 == 1

@pytest.mark.skipif('config.getoption("--run-mode") == "default"')
def test_log_parser():
    get_actual_endpoint_set()
    assert 1 == 1