import asyncio

import pytest

from core.config_dir.logger import log_event


@pytest.mark.skipif('config.getoption("--run-mode") != "ci_test"')
@pytest.mark.usefixtures('ac')
class TestBackgroundRender:
    @pytest.mark.parametrize(
        'cache, waited_instant_data',
        [
            (True, 'cached'),
            (False, ''),
        ]
    )
    @pytest.mark.asyncio
    async def test_bg_layout_ext_prd(self, ac, cache, waited_instant_data):
        prd_id, seller_id = 1, 1
        launch_hook = (await ac.get(f'/api/products/{prd_id}_{seller_id}', params={'in_front_cache': cache})).json()
        log_event(f'{launch_hook}', level='DEBUG')
        task_lvl1 = launch_hook['task-bg_lvl_1']
        task_lvl2 = launch_hook['task-bg_lvl_2']

        if cache:
            assert launch_hook['instantly_data'] == waited_instant_data
        else:
            assert launch_hook['instantly_data'].get('product')

        await asyncio.sleep(3)
        for idx, task_id in enumerate([task_lvl1, task_lvl2]):
            bg_res = await ac.get(f'/api/public/bg_tasks/{task_id}')
            assert bg_res.json()['success'] == True

    @pytest.mark.asyncio
    async def test_3lvl_bg(self, ac):
        task_id = (await ac.get('/api/products/bg_lvl3/1')).json()['task-bg_lvl_3']
        log_event(f'{task_id}', level='DEBUG')
        await asyncio.sleep(3)

        celery_res = await ac.get(f'/api/public/bg_tasks/{task_id}')
        assert celery_res.json()['success'] == True
