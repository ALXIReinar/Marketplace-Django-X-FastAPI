from starlette.websockets import WebSocket

from core.config_dir.logger import log_event
from core.utils.anything import Events
from core.utils.processing_data.jwt_utils.jwt_encode_decode import get_jwt_decode_payload


async def get_creds_open_online_connection(ws: WebSocket, encoded_ws_token: str):
    if (ws_token := get_jwt_decode_payload(encoded_ws_token, verify_exp=True)) == 401:
        # невалидный ws_токен / ws_токен ИСТЁК
        log_event(Events.fake_wT_try, level='CRITICAL')
        await ws.close(code=4001, reason='Попробуй перезайти')
        return
    return int(ws_token['sub']), ws_token['s_id']
