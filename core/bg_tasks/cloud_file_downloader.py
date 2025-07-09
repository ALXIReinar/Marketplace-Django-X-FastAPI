from fastapi import APIRouter, HTTPException
from starlette.requests import Request

from core.config_dir.config import env
from core.config_dir.logger import log_event
from core.data.s3_storage import S3Dep

router = APIRouter(prefix='/private/bg_tasks/s3_upload')



@router.put('/saving')
async def try_s3_save(file_path: str, request: Request, s3: S3Dep):
    log_event('Фоновая загрузка тяжёлого файла | file: %s', file_path, request=request)
    try:
        s3_path = '/'.join(file_path.split('_'))
        with open(f'{env.abs_path}/{env.bg_users_files}/{file_path}', 'rb') as f:
            await s3.save_file(f, s3_path)
    except FileNotFoundError:
        log_event('Файл не найден | %s', file_path, level='ERROR')
        raise HTTPException(status_code=404, detail='Файл не найден')
    except Exception as e:
        log_event('Неизвестная ошибка файла| file: %s | Exception: %s', file_path, e, level='CRITICAL')
        raise HTTPException(status_code=500, detail='Серверная ошибка')
    return {'success': True, 'message': 'В облако сохранён тяжёлый файл'}
