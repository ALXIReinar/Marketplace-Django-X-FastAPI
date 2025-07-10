import asyncio
import json
from pathlib import Path

import httpx
import pytest
from contextlib import nullcontext as no_raises

import requests
import websockets

from core.config_dir.config import env
from core.config_dir.logger import log_event
from core.schemas.chat_schema import WSControl
from tests.e2e.conftest import open_ws_link, start_ws_json, md5


@pytest.mark.usefixtures("ac")
class TestWS:
    """
    Советую запускать только целый класс. Отдельные тесты могут провалиться, тк зависят от других тестов
    """
    @pytest.mark.parametrize(
        'aT_val, rT_val, user_id',
        [
            ('2', 'session2', None),
            ('3', 'session3', 3),
        ]
    )
    @pytest.mark.asyncio
    async def test_ws_connection(self, ac, aT_val, rT_val, user_id):
        ws_link = await open_ws_link(ac, aT_val, rT_val)

        async with websockets.connect(ws_link) as webs:
            await webs.send(start_ws_json(1, user_id))
            last_messages = json.loads(await webs.recv())

        assert last_messages['event'] == WSControl.last_messages
        assert len(last_messages['messages']) == 3
        if user_id:
            assert last_messages['messages'][0]['first_unread'] == 0

    @pytest.mark.parametrize(
        'chat_id_u1, chat_id_u2, expect',
        [
            (1, 1, no_raises()),
            (1, 2, pytest.raises(AssertionError)),
        ]
    )
    @pytest.mark.asyncio
    async def test_ws_online_factor(self, ac, chat_id_u1, chat_id_u2, expect):
        ws_link1 = await open_ws_link(ac, '2', 'session2')
        ws_link2 = await open_ws_link(ac, '3', 'session3')

        with expect:
            async with websockets.connect(ws_link1) as ws1, websockets.connect(ws_link2) as ws2:
                await ws1.send(start_ws_json(chat_id_u1, None))
                await ws2.send(start_ws_json(chat_id_u2, None))

                res_user1 = json.loads(await ws1.recv())
                res_user2 = json.loads(await ws2.recv())

            assert res_user1 == res_user2

    @pytest.mark.asyncio
    async def test_receive_test_mes(self, ac):
        ws_link1 = await open_ws_link(ac, '2', 'session2')
        ws_link2 = await open_ws_link(ac, '3', 'session3')

        async with websockets.connect(ws_link1) as ws1, websockets.connect(ws_link2) as ws2:
            await ws1.send(start_ws_json(1, None))
            await ws2.send(start_ws_json(1, None))

            await ws1.recv()
            await ws2.recv()

            res_send = await ac.post(
                '/api/chats/send_message',
                cookies={'access_token': '2', 'refresh_token': 'session2'},
                json={"event": "send_msg", "chat_id": 1, "type": 1, "text_field": "test_string", "reply_id": None}
            )
            delivered_mes = json.loads(await ws2.recv())

        assert res_send.json()['success'] == True
        assert delivered_mes['msg_id'] == 6

    @pytest.mark.asyncio
    async def test_chats_layout(self, ac):
        await ac.put('/api/chats/commit_msg', json={'event': 'commit_msg', 'chat_id': 1, 'msg_id': 6})
        res_u1 = (await ac.get('/api/chats/', cookies={'access_token': '2', 'refresh_token': 'session2'})).json()
        res_u2 = (await ac.get('/api/chats/', cookies={'access_token': '3', 'refresh_token': 'session3'})).json()

        assert res_u1['chat_records'][0]['is_me'] == True and res_u1['chat_records'][0]['text_field'] == 'test_string'
        assert res_u2['chat_records'][0]['is_me'] == False and res_u2['chat_records'][0]['unread_count'] == 4

    async def test_set_readed_mes(self, ac):
        await ac.put('/api/chats/set_readed', json={"event": "set_readed", "chat_id": 1, "user_id": 3, "msg_id": 3})

        res_u2 = (await ac.get('/api/chats/', cookies={'access_token': '3', 'refresh_token': 'session3'})).json()
        assert res_u2['chat_records'][0]['unread_count'] == 1

    @pytest.mark.parametrize(
        'file_name, f_type, msg_id_eq',
        [
            ('test_img.png', "image/png", 7),
            ('test_40_mb.mp4', "video/mp4", 8),
        ]
    )
    @pytest.mark.asyncio
    async def test_s3_upload(self, prod_ac, ac, file_name, f_type, msg_id_eq):
        ws_link = await open_ws_link(ac, '2', 'session2')
        async with websockets.connect(ws_link) as ws:
            await ws.send(start_ws_json(1, None))
            await ws.recv()
            with open(f'{env.abs_path}{env.local_storage}/{file_name}', 'rb') as f:
                await prod_ac.post(
                    '/api/chats/send_file/s3',
                    files={
                        "file_obj": (file_name, f, f_type),
                        "file_hint": (None, '{"event":"save_file_s3","chat_id":1,"type":2,"text_field":null,"reply_id":null, "file_name": "' + file_name + '"}')
                    }
                )
            res = json.loads(await ws.recv())
            log_event(f'{res}', level='DEBUG')
            assert res['msg_id'] == msg_id_eq and res.get('file_name')
            await asyncio.sleep(5)
            ping = await prod_ac.post('/api/public/s3/long_ping', json={'key': f'users/chats/{res["file_name"]}'}, timeout=httpx.Timeout(90.0))
            assert ping.json()['success'] == True


    @pytest.mark.asyncio
    async def test_bulk_presigned_urls(self, ac):
        """
        Можно тестить отдельно
        """
        ws_link = await open_ws_link(ac, '2', 'session2')
        async with websockets.connect(ws_link) as ws:
            await ws.send(start_ws_json(1, None))
            await ws.recv()

            await ac.post(
                '/api/chats/bulk_presigned_urls',
                json={"event": "get_s3-obj_url", "chat_id": 1, "file_keys": ["users/chats/test_bulk1.png", "users/chats/test_bulk2.png"]}
            )
            links = json.loads(await ws.recv())
            log_event(f'{links}', level='DEBUG')
            for link in links['file_links'].values():
                assert requests.get(link).status_code == 200

    @pytest.mark.asyncio
    async def test_upload_local_file(self, ac):
        ws_link = await open_ws_link(ac, '2', 'session2')
        async with websockets.connect(ws_link) as ws:
            await ws.send(start_ws_json(1, None))
            await ws.recv()
            with open(f'.{env.local_storage}/test_img.png', 'rb') as f:
                await ac.post(
                    '/api/chats/send_file/local',
                    files={
                        "file_obj": ("test_img.png", f, "image/png"),
                        "file_hint": (None, '{"event":"save_file_fs","chat_id":1,"type":2,"text_field":null,"reply_id":null, "file_name": "test_img.png"}')
                    })
            res = json.loads(await ws.recv())
            assert res['success'] == True and res['msg_id'] == 9
            assert Path(f'.{env.local_storage}/users/chats/{res["file_name"]}').exists() == True


class TestLFS:
    @pytest.mark.asyncio
    async def test_file_response(self, ac):
        res = await ac.post(
            '/api/chats/get_file/local',
            json={"event": "get_file", "msg_type": 2, "file_path": "test_img.png"}
        )
        with open(f'.{env.local_storage}/test_img.png', 'rb') as f:
            original = f.read()
        assert res.content == original

    @pytest.mark.asyncio
    async def test_file_chunks(self, ac):
        async with ac.stream('POST', '/api/chats/get_file_chunks/local', json={"event": "get_chunks_file", "msg_type": 2, "file_path": "test_chunk_obj.mp4"}) as stream:
            chunks = []
            async for chunk in stream.aiter_bytes():
                chunks.append(chunk)
        with open(f'.{env.local_storage}/test_chunk_obj.mp4', 'rb') as f:
            original = f.read()
        assert md5(b"".join(chunks)) == md5(original)


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
        res = await ac.put('/api/server/crons/s3_fs-manager', timeout=httpx.Timeout(90))
        await asyncio.sleep(20)
        assert res.json()['message'].startswith(waited_res) == True
