import os
from time import sleep

from fastapi import APIRouter
from starlette.requests import Request

from core.config_dir.config import env
from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.data.s3_storage import S3Dep
from core.utils.anything import Events

router = APIRouter(prefix='/crons')



@router.delete('/flush_refresh-tokens')
async def flush_expired_rT(request: Request, db: PgSqlDep):
    log_event(Events.periodic_cron + 'Очистка рефреш_токенов', request=request, level='WARNING')
    await db.chats.remove_rubbish_messages()
    log_event(Events.cron_completed + "Истёкшие сессии удалены", request=request, level='WARNING')

@router.delete('/delete_chat-messages')
async def clear_trash_messages(request: Request, db: PgSqlDep):
    log_event(Events.periodic_cron + "Висячие сообщения удаляются", request=request, level='WARNING')
    await db.auth.slam_refresh_tokens()
    log_event(Events.cron_completed + "Мусорные сообщения удалены!", request=request, level='WARNING')

@router.put('/s3_fs-manager')
async def try_clear_bg_dir(s3: S3Dep):
    """
    Необходимо проверить на 2+ юви_воркерах, возможен конкурентный доступ
    """
    log_event(f'Крона на перевод файлов в С3 из /{env.bg_users_files}', level='WARNING')
    user_files = f'{env.abs_path}/{env.bg_users_files}'
    if len(os.listdir(user_files)) == 0:
        log_event('Объекты для S3 не обнаружены', level='WARNING')
        return {'success': True, 'message': 'Удалять нечего'}

    attempts = 0
    while len(os.listdir(user_files)) > 0:
        for file_path in os.listdir(user_files):
            file_key = file_path.replace('_', '/')
            if await s3.ping_object(file_key, env.s3_bucket_name):
                log_event('Удаляем файл! %s', file_path, level='WARNING')
                os.remove(f'{user_files}/{file_path}')
                log_event('Удалён из ФС | file: %s', file_path, level='WARNING')
            else:
                log_event('Файла не было в С3 | file_key: %s', file_key, level='WARNING')
                with open(f'{env.abs_path}/{env.bg_users_files}/{file_path}', 'rb') as f:
                    await s3.save_file(f, file_key)
        attempts += 1
        sleep(5)
    log_event('Очистка ФС успешна! | попытки: %s', attempts, level='WARNING')
    return {'success': True, 'message': f'Удалено с попытки: {attempts}'}
