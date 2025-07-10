import pytest

from core.config_dir.config import env
from core.data.redis_storage import get_redis_connection


@pytest.mark.usefixtures('ddos_ac')
class TestTrafficMiddleware:
    @pytest.mark.parametrize(
        'server_request, status_code',
        [
            (True, 200),
            (False, 429),
        ]
    )
    @pytest.mark.asyncio
    async def test_request_control_gt_limit(self, ddos_ac, server_request, status_code, ping_endpoint='/docs'):
        ips = {
            True: '127.0.0.1, 127.0.0.1',
            False: '222.0.222.0, 127.0.0.1'
        }
        res = None
        for _ in range(env.requests_limit + 1):
            res = (await ddos_ac.get(
                ping_endpoint,
                headers={'X-Forwarded-For': ips[server_request]}
            )).status_code

        assert res == status_code

    async def test_equals_redis_keys(self):
        async with get_redis_connection() as redis:
            server_count = await redis.get('127.0.0.1')
            other_count = (await redis.get('222.0.222.0')).decode()
            assert server_count is None
            assert other_count == str(env.requests_limit)
