import asyncio

import pytest

from core.config_dir.config import env


@pytest.mark.usefixtures('ac')
class TestSimpleCrons:
    @pytest.mark.asyncio
    async def test_rT_cleaner(self, ac):
        await ac.delete('/api/server/crons/flush_refresh-tokens')
        await asyncio.sleep(3)
        db_confirmation = await ac.post(
            env.pg_api_db,
            json={'query': 'select count(*) from sessions_users where exp < now()', 'method': 'fetchrow'}
        )
        assert db_confirmation.json()['result']['count'] == 0 or db_confirmation.json()['result']['count'] == 3

    @pytest.mark.asyncio
    async def test_messages_cleaner(self, ac):
        await ac.delete('/api/server/crons/delete_chat-messages')
        await asyncio.sleep(1)
        db_confirmation = await ac.post(
            env.pg_api_db,
            json={'query': 'select count(*) from chat_messages where is_commited = false', 'method': 'fetchrow'}
        )
        assert db_confirmation.json()['result']['count'] == 0


@pytest.mark.skipif('config.getoption("--run-mode") != "ci_test"')
@pytest.mark.usefixtures('ac', 'cp_test_objects')
class TestS3Crons:
    @pytest.mark.parametrize(
        'waited_res',
        [
            'Удалено с попытки: ',
            'Удалять нечего',
        ]
    )
    @pytest.mark.asyncio
    async def test_s3_kharon(self, ac, waited_res):
        res = await ac.post('/api/server/crons/s3_fs-manager')
        await asyncio.sleep(20)

        assert res.json()['message'].startswith(waited_res) == True
