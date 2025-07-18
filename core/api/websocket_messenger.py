import asyncio
import json
import os.path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Form, UploadFile
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

from core.config_dir.base_dependencies import PagenChatDep
from core.config_dir.config import broadcast, env
from core.config_dir.logger import log_event
from core.bg_tasks.celery_processing import bg_s3_upload
from core.data.postgre import PgSqlDep, PgSql, set_connection
from core.data.s3_storage import S3Dep
from core.schemas.chat_schema import WSOpenCloseSchema, WSMessageSchema, PaginationChatMessSchema, ChatSaveFiles, \
    WSFileSchema, WSReadUpdateSchema, WSCommitMsgSchema, WSPresignedLinkSchema, WSControl, WSFileChunksSchema
from core.utils.anything import Tags, cut_log_param
from core.utils.file_cutter import content_cutter, cutter_types
from core.utils.processing_data.jwt_utils.jwt_factory import issue_token
from core.utils.processing_data.raw_fields_to_pydantic import parse_raw_schema
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
    return {'ws_token': ws_token, 'user_id': request.state.user_id}


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

    chat_channel = f"{WSControl.ws_chat_channel}:{contract_obj.chat_id}"
    "Получаем последние сообщения"
    pool = await set_connection()
    async with pool.acquire() as conn:
        db = PgSql(conn)
        last_chat_messages = await db.chats.get_chat_messages(contract_obj.chat_id, pagen.limit, pagen.offset, contract_obj.user_id)
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
    except Exception as e:
        task.cancel()
        log_event("Вебсокет закрылся! | Exception: %s | user_id: %s; chat_id: %s",
                  e, user_id, contract_obj.chat_id, request=ws, level='WARNING')


@router.post('/send_message')
async def send_json_ws(contract_obj: WSMessageSchema, request: Request, db: PgSqlDep):
    saved_msg_json = await db.chats.save_message(
        chat_id=contract_obj.chat_id,
        user_id=request.state.user_id,
        msg_type=contract_obj.type,
        text_field=contract_obj.text_field,
        reply_id=contract_obj.reply_id
    )
    log_event("Сохранено сообщение #%s; chat_id: %s", saved_msg_json['msg_id'], contract_obj.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{contract_obj.chat_id}', message=json.dumps(saved_msg_json))
    return {'success': True, 'message': 'Сохранено, лови msg_id!'}


@router.post('/send_file/local')
async def absorb_binary(
        file_hint: Annotated[str, Form(
            example='{"event":"save_file_fs","chat_id":4,"type":2,"text_field":null,"reply_id":null,"file_name":"example.png"}'
        )],
        file_obj: UploadFile,
        request: Request,
        db: PgSqlDep,
):
    """
    ОБЯЗАТЕЛЬНО ПОСТАВЬ ОГРАНИЧЕНИЕ НА ФАЙЛЫ - НЕ БОЛЬШЕ 250MB НА СТОРОНЕ ФРОНТА
    """
    file_hint = parse_raw_schema(file_hint, ChatSaveFiles)

    log_event('Загрузка файла: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    uniq_id = str(uuid4())
    ext = os.path.splitext(file_hint.file_name)[-1]
    db_file_name =f'users/chats/{uniq_id}{ext}'
    try:
        with open(f'{env.abs_path}{env.local_storage}/{db_file_name}', 'wb') as f:
            f.write(file_obj.file.read())
    except OSError as oe:
        log_event('Проблемы с ОС сервера | file: %s | Exception: %s', db_file_name, oe, level='CRITICAL')
        raise HTTPException(status_code=500, detail='Проблемы сервером')
    except Exception as e:
        log_event('Непредвиденная ошибка при записи в локальную ФС | file: %s | Exception: %s',
                  db_file_name, e, level='CRITICAL')
        raise HTTPException(status_code=500, detail='Проблемы сервером')

    saved_msg_json = await db.chats.save_message(
        chat_id=file_hint.chat_id,
        user_id=request.state.user_id,
        msg_type=file_hint.type,
        text_field=file_hint.text_field,
        content_path=db_file_name,
        reply_id=file_hint.reply_id
    )
    saved_msg_json['file_name'] = uniq_id
    log_event('Файл Сохранён локально!: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{file_hint.chat_id}', message=json.dumps(saved_msg_json))
    return {'success': True, 'message': 'Сохранено, лови uuid!'}


@router.post('/get_file/local')
async def get_binary_file(file_obj: WSFileSchema, request: Request):
    """
    Допускается только:
    chat_messages:
     - type: 2 - media, только фото!!!
             4 - doc
    """
    log_event('Отправлен файл: user_id: %s; s_id: %s; file_type: %s',
              request.state.user_id, request.state.session_id, file_obj.msg_type, request=request)
    return FileResponse(f'.{env.local_storage}/{file_obj.file_path}', media_type='application/octet-stream')


@router.post('/get_file_chunks/local')
async def get_chunks_file(file_obj: WSFileChunksSchema, request: Request):
    """
    Допускается только:
    chat_messages:
     - type: 2 - media, только видео!!!
             3 - audio
    """
    log_event('Стриминг файла: %s, msg_type: %s; user_id: %s', file_obj.file_path, file_obj.msg_type, request.state.user_id, request=request)
    return StreamingResponse(content_cutter(file_obj.file_path), media_type=cutter_types[file_obj.msg_type])


"S3 Storage Save Binary"
@router.post('/send_file/s3')
async def save_to_bucket(
        file_hint: Annotated[str, Form(
            example='{"event":"save_file_s3","chat_id":4,"type":2,"text_field":null,"reply_id":null,"file_name":"example.png"}'
        )],
        file_obj: UploadFile,
        request: Request,
        db: PgSqlDep,
        s3: S3Dep
):
    """
    ОБЯЗАТЕЛЬНО ПОСТАВЬ ОГРАНИЧЕНИЕ НА ФАЙЛЫ - НЕ БОЛЬШЕ 250MB
    """
    file_hint = parse_raw_schema(file_hint, ChatSaveFiles)

    log_event('Загрузка файла: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    uniq_id = str(uuid4())
    ext = os.path.splitext(file_hint.file_name)[-1]
    db_file_name =f'users/chats/{uniq_id}{ext}'
    if file_obj.size <= env.bg_upload_file_size:
        await s3.save_file(file_obj, db_file_name)
    else:
        try:
            with open(f'{env.abs_path}/{env.bg_users_files}/users_chats_{uniq_id}{ext}', 'wb') as f:
                f.write(file_obj.file.read())
        except OSError as oe:
            log_event('Проблемы с ОС сервера | file: %s | Exception: %s', db_file_name, oe, level='CRITICAL')
            raise HTTPException(status_code=500, detail='Проблемы сервером')
        except Exception as e:
            log_event('Непредвиденная ошибка при записи в ФС для дампа тяжёлого файла | file: %s | Exception: %s',
                      db_file_name, e, level='CRITICAL')
            raise HTTPException(status_code=500, detail='Проблемы сервером')
        bg_s3_upload.delay(f'users_chats_{uniq_id}{ext}')

    saved_msg_json = await db.chats.save_message(
        chat_id=file_hint.chat_id,
        user_id=request.state.user_id,
        msg_type=file_hint.type,
        text_field=file_hint.text_field,
        content_path=db_file_name,
        reply_id=file_hint.reply_id
    )
    saved_msg_json['file_name'] = uniq_id
    log_event('Файл Сохранён в Облако!: %s; user_id: %s; chat_id: %s', file_hint.file_name, request.state.user_id, file_hint.chat_id, request=request)
    await broadcast.publish(f'{WSControl.ws_chat_channel}:{file_hint.chat_id}', message=json.dumps(saved_msg_json))
    return {'success': True, 'message': 'Сохранено, лови uuid!'}

@router.post('/bulk_presigned_urls')
async def give_s3_object_urls(s3_req: WSPresignedLinkSchema, request: Request, s3: S3Dep):
    pre_urls: dict[str, str] = dict()
    log_event('Начало выдачи ссылок на s3-объекты в кол-ве: %s', len(s3_req.file_keys), request=request, level='WARNING')

    for idx, file in enumerate(s3_req.file_keys, 1):
        pre_url = await s3.set_presigned_url(file)
        pre_urls[file] = pre_url

    await broadcast.publish(f'{WSControl.ws_chat_channel}:{s3_req.chat_id}', json.dumps({'file_links': pre_urls}))
    log_event('Бульк на s3-ссылки Отработал! | %s', len(pre_urls), request=request, level='WARNING')
    return {'success': True, 'message': 'Доступ к объектам из S3'}


@router.put('/set_readed')
async def update_read_count(contract_obj: WSReadUpdateSchema, request: Request, db: PgSqlDep):
    await db.chats.update_readed_messages(contract_obj.user_id, contract_obj.chat_id, contract_obj.msg_id)
    log_event("Новые прочитанные сообщения | user_id: %s; chat_id: %s; msg_local_id: %s",
              contract_obj.user_id, contract_obj.chat_id, contract_obj.msg_id, request=request)
    return {'success': True, 'message': 'Счётчик обновлён'}


@router.put('/commit_msg')
async def commit_message(contract_obj: WSCommitMsgSchema, request: Request, db: PgSqlDep):
    await db.chats.commit_message(contract_obj.chat_id, contract_obj.msg_id)
    log_event('Сообщение утверждено и отправлено | chat_id: %s; msg_local_id: %s', contract_obj.chat_id, contract_obj.msg_id, request=request)
    return {'success': True, 'message': 'Коммит сообщения успешен!'}
