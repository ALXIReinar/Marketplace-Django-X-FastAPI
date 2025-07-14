import hashlib
import json
import shutil
from pathlib import Path

import pytest

from core.config_dir.config import get_uvicorn_host, env


async def open_ws_link(ac, aT_val, rT_val):
    res = await ac.get('/api/chats/get_ws_token', cookies={'access_token': aT_val, 'refresh_token': rT_val})
    return f'ws://{get_uvicorn_host()}:8000/api/chats/ws?ws_token={res.json()["ws_token"]}&limit=40&offset=0'

def start_ws_json(chat_id, user_id):
    return json.dumps({
        'event': 'view_chat',
        'chat_id': chat_id,
        'user_id': user_id
    })

def md5(data):  return hashlib.md5(data).hexdigest()


@pytest.fixture(scope='session')
def cp_test_objects():
    lite_obj = Path(f'{env.abs_path}{env.local_storage}/test-img.png')
    heavy_obj = Path(f'{env.abs_path}{env.local_storage}/test-40-mb.mp4')
    destination = Path(f'{env.abs_path}/{env.bg_users_files}')

    shutil.copy(lite_obj, destination)
    shutil.copy(heavy_obj, destination)
