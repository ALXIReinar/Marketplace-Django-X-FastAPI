import json

from broadcaster import Broadcast
from starlette.websockets import WebSocket


async def pub_sub(channel: str, broadcast: Broadcast, ws: WebSocket):
    async with broadcast.subscribe(channel=channel) as subs:
        async for update in subs:
            update_json = json.loads(update.message)
            await ws.send_json(update_json)
