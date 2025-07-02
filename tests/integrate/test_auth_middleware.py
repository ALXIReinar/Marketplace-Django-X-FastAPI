import pytest

from core.config_dir.logger import log_event
from tests.integrate.conftest import get_urls_plan

@pytest.mark.usefixtures('ac', 'ac_methods')
class TestAuthUXMiddleware:
    @pytest.mark.parametrize(
        'method, endpoint, ip, waited_code',
        get_urls_plan(cookies=False)
    )
    @pytest.mark.asyncio
    async def test_auth_control_wo(self, ac_methods, method, endpoint, ip, waited_code):
        res = await ac_methods[method](endpoint, headers={'X-Forwarded-For': ip})
        log_event(f'{res}', level='DEBUG')
        assert res.status_code == waited_code


    @pytest.mark.parametrize(
        'method, endpoint, ip, waited_code, cookie_count',
        get_urls_plan(cookies=True)
    )
    @pytest.mark.asyncio
    async def test_auth_control_w_cookies(self, ac_methods, method, endpoint, ip, waited_code, cookie_count):
        cookies = {'access_token': '1'}
        if cookie_count == 2:
            cookies['refresh_token'] = '2'

        res = await ac_methods[method](endpoint, headers={'X-Forwarded-For': ip}, cookies=cookies)
        assert res.status_code == waited_code

@pytest.mark.skipif('config.getoption("--run-mode") == "default"')
def test_get_actual_endpoint_set():
    get_urls_plan(cookies=False)
    assert 1 == 1
