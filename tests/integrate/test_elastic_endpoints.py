import pytest

from core.config_dir.logger import log_event

@pytest.mark.skipif('config.getoption("--run-mode") != "elastic"')
@pytest.mark.usefixtures('prepare_elasticsearch', 'ac')
class TestSearch:
    @pytest.mark.parametrize(
        'index_name, result',
        [
            ('test_index1', True),
            ('test_index2', False),
            ('test_index3', False),
        ]
    )
    @pytest.mark.asyncio
    async def test_index_up(self, ac, index_name, result):
        res = await ac.put(f'/api/elastic/index_up/{index_name}')
        assert res.json()['success'] == result

    @pytest.mark.parametrize(
        'search_word, waited_res',
        [
            ('test', 3),
            ('clathe', 1)
        ]
    )
    @pytest.mark.asyncio
    async def test_searching(self, ac, search_word, waited_res):
        res = await ac.post(
            '/api/products/elastic/search',
            json={'text': search_word}
        )
        assert len(res.json()['products']) == waited_res
