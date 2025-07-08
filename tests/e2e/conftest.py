import hashlib
import json

from core.config_dir.config import get_uvicorn_host


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