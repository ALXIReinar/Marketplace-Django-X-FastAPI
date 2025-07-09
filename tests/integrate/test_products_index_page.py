import pytest

from core.config_dir.logger import log_event


@pytest.mark.parametrize(
    'cookies, counters, len_layout',
    [
        ({'access_token': '2', 'refresh_token': 'test_session1'}, (4, 0, 2), 3),
        ({'access_token': '3', 'refresh_token': 'test_session2'}, (0, 2, 2), 2),
    ]
)
@pytest.mark.asyncio
async def test_index_page(prod_ac, xff_ip, cookies, counters, len_layout):
    res = (await prod_ac.post(
        '/api/products/',
        cookies=cookies,
        headers=xff_ip,
        params={'limit': 60, 'offset': 0}
    )).json()

    log_event(f'{res}', level='DEBUG')

    assert len(res['products']) == len_layout
    for idx, count in enumerate(res['counters'].values()):
        assert count == counters[idx]
