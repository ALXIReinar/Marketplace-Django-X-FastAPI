import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from starlette.requests import Request
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.config_dir.base_dependencies import PagenChatDep
from core.config_dir.config import broadcast
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep, init_pool
from core.schemas.chat_schema import WSOpenCloseSchema, WSMessageSchema, PaginationChatMessSchema
from core.utils.anything import Tags, WSControl
from core.utils.processing_data.jwt_utils.jwt_factory import issue_token
from core.utils.websocket_tools.broadcast_channel import pub_sub
from core.utils.celery_serializer import convert
from core.utils.websocket_tools.ws_auth_ware import get_creds_open_online_connection

router = APIRouter(prefix='/api/chats', tags=[Tags.chat])



@router.get('/')
async def get_chats(pagen: PagenChatDep, request: Request, db: PgSqlDep):
    """
    state sheets:
    - 0 - deleted
    - 1 - active
    - 2 - blocked

    chat_messages:
     - type: 1 - text
             2 - media
             3 - audio
    """
    chats = await db.chats.get_user_chats(request.state.user_id, pagen.limit, pagen.offset)
    return {'chat_records': chats}


@router.get('/get_ws_token')
async def throw_wT(request: Request):
    payload = {
        'sub': str(request.state.user_id),
        's_id': request.state.session_id
    }
    ws_token = await issue_token(payload, 'ws_token')
    log_event("Выдан ws_token: %s", ws_token, request=request)
    return {'ws_token': ws_token}


@router.websocket('/ws')
async def ws_control(ws: WebSocket):
    await ws.accept()
    try:
        "Получаем арги из URL"
        pagen = PaginationChatMessSchema(**dict(ws.query_params))
        log_event("ws_token: %s", pagen.ws_token, level='DEBUG')
        if (creds:= await get_creds_open_online_connection(ws, pagen.ws_token)) is None:
            return
        user_id, s_id = creds
        "Ждём Тело запроса"
        json_obj = await ws.receive_json()
        contract_obj = WSOpenCloseSchema(**json_obj)
    except ValidationError as ve:
        log_event("Валидация провалилась | Exception: %s", ve, request=ws, level='ERROR')
        raise WebSocketDisconnect(code=4220, reason='Ошибка в данных')
    except Exception as e:
        log_event("Неучтённая Ошибка!!! | Exception: %s", e, request=ws, level='CRITICAL')
        raise WebSocketDisconnect(code=4000, reason='Exception')

    log_event('ws_token: %s - accepted!', pagen.ws_token, request=ws, level='DEBUG')
    if contract_obj.event == WSControl.open:
        chat_channel = f"{WSControl.ws_chat_channel}:{contract_obj.chat_id}"

        "Получаем последние сообщения"
        async with init_pool() as db:
            last_chat_messages = await db.chats.get_chat_messages(contract_obj.chat_id, pagen.limit, pagen.offset)
        log_event("Отданы сообщения: %s; chat_id: %s", len(last_chat_messages), contract_obj.chat_id, request=ws)
        await ws.send_json({'event': WSControl.last_messages, "messages":convert(last_chat_messages)})

        "Открываем вещание"
        task = asyncio.create_task(
            pub_sub(chat_channel, broadcast, ws)
        )
        try:
            while True:
                json_data = await ws.receive_json()
                await broadcast.publish(channel=chat_channel, message=json_data)
                log_event("message: %s; channel: %s", json_data, chat_channel, request=ws, level='DEBUG')
        except Exception as e:
            task.cancel()
            log_event("Вебсокет закрылся! | Exception: %s | user_id: %s; chat_id: %s",
                      e, user_id, contract_obj.chat_id, request=ws, level='WARNING')


@router.post('/send_message')
async def send_json_ws(contract_obj: WSMessageSchema, request: Request, db: PgSqlDep):
    if contract_obj.event != WSControl.send_msg:
        raise HTTPException(status_code=403, detail={'success': False, 'message': 'Фронт, не то событие передал для JSON'})

    saved_msg_id = await db.chats.save_message(
        chat_id=contract_obj.chat_id,
        user_id=request.state.user_id,
        msg_type=contract_obj.type,
        text_field=contract_obj.text_field,
        reply_id=contract_obj.reply_id
    )
    log_event("Сохранено сообщение #%s; chat_id: %s", saved_msg_id, contract_obj.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{contract_obj.chat_id}', message={'success': True, 'msg_id': saved_msg_id})


