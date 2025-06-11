import asyncio

from fastapi import APIRouter, HTTPException
from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.base_dependencies import PagenChatDep, PagenChatMessDep
from core.config_dir.config import broadcast
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.schemas.chat_schema import WSOpenCloseSchema, WSMessageSchema
from core.utils.anything import Tags, WSControl
from core.utils.broadcast_channel import pub_sub
from core.utils.celery_serializer import convert

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


@router.websocket('/ws')
async def ws_control(contract_obj: WSOpenCloseSchema, pagen: PagenChatMessDep, ws: WebSocket, request: Request, db: PgSqlDep):
    await ws.accept()
    if contract_obj.event == WSControl.open:
        chat_channel = f"{WSControl.ws_chat_channel}:{contract_obj.chat_id}"

        "Получаем последние сообщения"
        last_chat_messages = await db.chats.get_chat_messages(contract_obj.chat_id, pagen.limit, pagen.offset)
        log_event("Отданы сообщения: %s; chat_id: %s", len(last_chat_messages), contract_obj.chat_id, request=request)
        await ws.send_json({'event': WSControl.last_messages, "messages":convert(last_chat_messages)})

        "Открываем вещание"
        task = asyncio.create_task(
            pub_sub(chat_channel, broadcast, ws)
        )
        try:
            while True:
                json_data = await ws.receive_json()
                await broadcast.publish(channel=chat_channel, message=json_data)
                log_event("message: %s; channel: %s", json_data, chat_channel, level='DEBUG')
        except Exception as e:
            task.cancel()
            log_event("Вебсокет закрылся! | Exception: %s | user_id: %s; chat_id: %s",
                      e, request.state.user_id, contract_obj.chat_id, request=request, level='WARNING')


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


