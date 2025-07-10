import asyncio
from botocore.exceptions import ClientError
from fastapi import APIRouter

from core.config_dir.logger import log_event
from core.data.s3_storage import S3Dep
from core.schemas.chat_schema import WSPingS3Schema

router = APIRouter(prefix='/api/public')



@router.post('/s3/long_ping')
async def wait_for_object(ping_sch: WSPingS3Schema, s3: S3Dep):
    elapsed = 0
    while elapsed < ping_sch.timeout:
        res = await s3.ping_object(bucket_name=s3.bucket, file_key=ping_sch.key)
        if res:
            return {'success': True, 'message': 'Объект в С3'}
        else:
            await asyncio.sleep(ping_sch.interval)
            elapsed += ping_sch.interval
    return {'success': False, 'message': 'Объект не сохранился в С3, Таймаут'}
