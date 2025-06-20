import asyncio
import json
import os.path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, Form
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.config_dir.base_dependencies import PagenChatDep
from core.config_dir.config import broadcast, env
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep, init_pool
from core.schemas.chat_schema import WSOpenCloseSchema, WSMessageSchema, PaginationChatMessSchema, ChatSaveFiles, \
    WSFileSchema
from core.utils.anything import Tags, WSControl, cut_log_param
from core.utils.file_cutter import content_cutter, cutter_types
from core.utils.processing_data.jwt_utils.jwt_factory import issue_token
from core.utils.processing_data.raw_fields_to_pydantic import parse_schema
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
             4 - doc
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
    log_event("Выдан ws_token: %s", cut_log_param(ws_token), request=request)
    return {'ws_token': ws_token}


@router.websocket('/ws')
async def ws_control(ws: WebSocket):
    await ws.accept()
    try:
        "Получаем арги из URL"
        pagen = PaginationChatMessSchema(**dict(ws.query_params))
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

    if contract_obj.event == WSControl.open:
        chat_channel = f"{WSControl.ws_chat_channel}:{contract_obj.chat_id}"

        "Получаем последние сообщения"
        async with init_pool() as db:
            last_chat_messages = await db.chats.get_chat_messages(contract_obj.chat_id, pagen.limit, pagen.offset)
        log_event("Открыт ВебСокет; Отданы сообщения: %s; chat_id: %s", len(last_chat_messages), contract_obj.chat_id, request=ws)
        await ws.send_json({'event': WSControl.last_messages, "messages": convert(last_chat_messages)})

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
    raise WebSocketDisconnect(code=4001, reason='Неверные данные!')


@router.post('/send_message')
async def send_json_ws(contract_obj: WSMessageSchema, request: Request, db: PgSqlDep):
    if contract_obj.event != WSControl.send_msg:
        raise HTTPException(status_code=403, detail={'success': False, 'message': 'Фронт, не то событие передал для JSON'})

    saved_msg_json = await db.chats.save_message(
        chat_id=contract_obj.chat_id,
        user_id=request.state.user_id,
        msg_type=contract_obj.type,
        text_field=contract_obj.text_field,
        reply_id=contract_obj.reply_id
    )
    log_event("Сохранено сообщение #%s; chat_id: %s", saved_msg_json['msg_id'], contract_obj.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{contract_obj.chat_id}', message=json.dumps(saved_msg_json))



@router.post('/send_file/local')
async def absorb_binary(
        file_hint: Annotated[str, Form()],
        file_obj: UploadFile,
        request: Request,
        db: PgSqlDep,
):
    file_hint = parse_schema(file_hint, ChatSaveFiles)

    if file_hint.event != WSControl.save_file:
        raise HTTPException(status_code=403, detail={'success': False, 'message': 'Фронт, не то событие передал в JSON'})

    log_event('Загрузка файла: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    uniq_id = uuid4()
    ext = os.path.splitext(file_hint.file_name)[-1]
    db_file_name =f'{env.local_storage}/{uniq_id}{ext}'
    with open(f'.{db_file_name}', 'wb') as f:
        f.write(file_obj.file.read())

    saved_msg_json = await db.chats.save_message(
        chat_id=file_hint.chat_id,
        user_id=request.state.user_id,
        msg_type=file_hint.type,
        text_field=file_hint.text_field,
        content_path=db_file_name,
        reply_id=file_hint.reply_id
    )
    log_event('Файл Сохранён!: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{file_hint.chat_id}', message=json.dumps(saved_msg_json))


@router.get('/get_file/local')
async def get_binary_file(file_obj: WSFileSchema, request: Request):
    """
    Допускается только:
    chat_messages:
     - type: 2 - media, только фото!!!
             4 - doc
    """
    if file_obj.event != WSControl.get_file or file_obj.msg_type in (1, 3):
        raise HTTPException(status_code=403, detail={'success': False, 'message': 'Фронт, не то событие или тип сообщения!'})

    log_event('Отправлен файл: user_id: %s; s_id: %s; file_type: %s',
              request.state.user_id, request.state.session_id, file_obj.msg_type, request=request)
    return FileResponse(f'.{file_obj.file_path}', media_type='application/octet-stream')


@router.get('/get_file_chunks/local')
async def get_chunks_file(file_obj: WSFileSchema, request: Request):
    """
    Допускается только:
    chat_messages:
     - type: 2 - media, только видео!!!
             3 - audio
    """
    if file_obj.event != WSControl.get_file or file_obj.msg_type in (1, 4):
        raise HTTPException(status_code=403, detail={'success': False, 'message': 'Фронт, не то событие или тип передал'})

    log_event('Стриминг файла: %s, msg_type: %s', file_obj.file_path, file_obj.msg_type, request.state.user_id, request=request)
    return StreamingResponse(content_cutter(file_obj.file_path), media_type=cutter_types[file_obj.msg_type])
