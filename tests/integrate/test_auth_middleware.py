import pytest

from tests.integrate.conftest import get_urls_plan

@pytest.mark.usefixtures('auth_ac', 'auth_ac_methods')
class TestAuthUXMiddleware:
    @pytest.mark.parametrize(
        'method, endpoint, ip, waited_code',
        get_urls_plan(cookies=False)
    )
    @pytest.mark.asyncio
    async def test_auth_control_wo(self, auth_ac_methods, method, endpoint, ip, waited_code):
        res = await auth_ac_methods[method](endpoint, headers={'X-Forwarded-For': ip})
        assert res.status_code == waited_code


    @pytest.mark.parametrize(
        'method, endpoint, ip, waited_code, cookie_count',
        get_urls_plan(cookies=True)
    )
    @pytest.mark.asyncio
    async def test_auth_control_w_cookies(self, auth_ac_methods, method, endpoint, ip, waited_code, cookie_count):
        cookies = {'access_token': '1'}
        if cookie_count == 2:
            cookies['refresh_token'] = '2'

        res = await auth_ac_methods[method](endpoint, headers={'X-Forwarded-For': ip}, cookies=cookies)
        assert res.status_code == waited_code

@pytest.mark.skipif('config.getoption("--run-mode") != "stress"')
def test_get_actual_endpoint_set():
    get_urls_plan(cookies=False)
    assert 1 == 1
