import pytest


@pytest.mark.skipif('config.getoption("--run-mode") != "ci_test"')
@pytest.mark.usefixtures('prepare_elasticsearch', "prod_ac")
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
    async def test_index_up(self, prod_ac, index_name, result):
        res = await prod_ac.put(f'/api/elastic/index_up/{index_name}')
        assert res.json()['success'] == result

    @pytest.mark.parametrize(
        'search_word, waited_res',
        [
            ('test', 3),
            ('clathe', 1)
        ]
    )
    @pytest.mark.asyncio
    async def test_searching(self, prod_ac, search_word, waited_res):
        res = await prod_ac.post(
            '/api/products/elastic/search',
            json={'text': search_word}
        )
        assert len(res.json()['products']) == waited_res
