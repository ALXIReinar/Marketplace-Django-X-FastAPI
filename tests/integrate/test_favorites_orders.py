import pytest

from core.config_dir.logger import log_event


@pytest.mark.usefixtures("ac")
class TestOrders:
    @pytest.mark.parametrize(
        'cookies_vals, counters',
        [
            (('2', 'test_session1'), (0, 2, 2)),
            (('3', 'test_session2'), (1, 1, 1)),
        ]
    )
    @pytest.mark.asyncio
    async def test_orders_counters(self, ac, xff_ip, cookies_vals, counters):
        res = await ac.get(
            '/api/orders/',
            cookies={'access_token': cookies_vals[0], 'refresh_token': cookies_vals[1]},
            headers=xff_ip
        )
        assert res.json() == {'success': True, 'orders_counts': {
            'actual': counters[0], 'completed': counters[1], 'purchased': counters[2]
        }}

    @pytest.mark.parametrize(
        'tab, cookies_vals, len_waited_json',
        [
            (True, ('2', 'test_session1'), 2),
            (False, ('2', 'test_session1'), 0),
            (True, ('3', 'test_session2'), 1),
            (False, ('3', 'test_session2'), 1),
        ]
    )
    @pytest.mark.asyncio
    async def test_orders_tab(self, ac, xff_ip, tab, cookies_vals, len_waited_json):
        res = await ac.get(
            '/api/orders/sections',
            headers=xff_ip,
            cookies={'access_token': cookies_vals[0], 'refresh_token': cookies_vals[1]},
            params={'status': tab, 'limit': 60, 'offset': 0}
        )
        assert len(res.json()['order_products']) == len_waited_json

    @pytest.mark.parametrize(
        'cookies_vals, waited_len_json',
        [
            (('2', 'test_session1'), 2),
            (('3', 'test_session2'), 1),
        ]
    )
    @pytest.mark.asyncio
    async def test_buy_again_products(self, ac, xff_ip, cookies_vals, waited_len_json):
        res = await ac.get(
            '/api/orders/purchased',
            headers=xff_ip,
            cookies={'access_token': cookies_vals[0], 'refresh_token': cookies_vals[1]},
            params={'limit': 40, 'offset': 0}
        )
        assert len(res.json()['purchased_products']) == waited_len_json


@pytest.mark.usefixtures("ac")
class TestFavorite:
    @pytest.mark.parametrize(
        'cookies_vals, waited_len_json',
        [
            (('2', 'test_session1'), 4),
            (('3', 'test_session2'), 0),
        ]
    )
    @pytest.mark.asyncio
    async def test_layout_favorite(self, ac, xff_ip, cookies_vals, waited_len_json):
        res = await ac.get(
            '/api/favorites/',
            cookies={'access_token': cookies_vals[0], 'refresh_token': cookies_vals[1]},
            headers=xff_ip,
            params={'limit': 20, 'offset': 0}
        )
        assert len(res.json()['favorite_products']) == waited_len_json
