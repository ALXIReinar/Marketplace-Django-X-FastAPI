import json

import pytest
from unittest.mock import patch

import websockets

from core.config_dir.config import get_uvicorn_host
from core.config_dir.logger import log_event
from core.schemas.chat_schema import WSControl


@pytest.mark.usefixtures('ac')
class TestWS:
    @pytest.mark.asyncio
    async def test_ws_connection(self):
        with patch(
                "core.api.websocket_messenger.get_creds_open_online_connection",
                new=lambda websocket, ws_token: (2, 'session_test_user1')
        ):
            ws_link = f'ws://{get_uvicorn_host()}:8000/api/chats/ws?ws_token=test_token1&limit=30&offset=0'
            async with websockets.connect(ws_link) as ws:
                await ws.send(json.dumps({
                    'event': 'view_chat',
                    'chat_id': 1,
                    'user_id': None
                }))
                last_messages = json.loads(await ws.recv())
                log_event(f'{last_messages}', level='DEBUG')
            assert last_messages['event'] == WSControl.last_messages
            assert len(last_messages['messages']) == 3

    # @pytest.mark.parametrize(
    #     ''
    # )
    # @pytest.mark.asyncio
    # async def test_ws_online_factor(self):
    #     ...