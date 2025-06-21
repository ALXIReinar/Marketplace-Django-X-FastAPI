import os
from typing import Annotated

from fastapi import HTTPException
from fastapi.params import Depends
from starlette.datastructures import UploadFile

from core.config_dir.config import cloud_session, get_env_vars, env
from core.config_dir.logger import log_event


class S3Storage:
    def __init__(
            self,
            _cloud_session,
            bucket_name,
    ):
        self.bucket = bucket_name
        self.session = _cloud_session


    async def save_file(self, uploaded_file, file_path: str, heavy_file: bool = False):
        log_event('Файл сохраняется в С3 | file: %s', file_path)
        log_event('передаю объект с типом: %s; сам тип в сравнении: %s', type(uploaded_file), UploadFile, level='DEBUG')
        if isinstance(uploaded_file, UploadFile):
            f = await uploaded_file.read()
            content_length = len(f)
        else:
            f = uploaded_file
            seeker = f.seek(0, os.SEEK_END)
            content_length = seeker.tell()
            f.seek(0) # Проверка на file-like объект, а не bytes | str

        try:
            await self.session.put_object(
                Bucket=self.bucket,
                Key=f'{env.cloud_storage}/{file_path}',
                Body=f,
                ContentLength=content_length
            )
        except Exception as e:
            log_event('Ошибка сохранения файла в С3! | %s', e, level='CRITICAL')
            raise HTTPException(status_code=504, detail={'success': False, 'message': 'Ошибка загрузки файла'})
        log_event('Записан Файл в S3 \033[35m(Уровень Облака)\033[0m | file: %s', file_path)

        if heavy_file:
            log_event('Удаление файла %s', file_path, level='WARNING')
            os.remove(f'{env.abs_path}/user_files_bg_dumps')
            log_event('Файл Удалён! %s', file_path, level='WARNING')


    async def set_presigned_url(self, file_key: str, ttl: int = 3600):
        params = {
            'Bucket': self.bucket,
            'Key': f'{env.cloud_storage}/{file_key}'
        }
        presigned_url = await self.session.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=ttl
        )
        log_event('Выдан юрл на s3-объект: %s', file_key)
        return presigned_url



async def set_cloud_session():
    async with cloud_session() as cloud:
        yield S3Storage(cloud, get_env_vars().s3_bucket_name)

S3Dep = Annotated[S3Storage, Depends(set_cloud_session)]
