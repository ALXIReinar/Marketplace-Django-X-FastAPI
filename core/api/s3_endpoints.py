import asyncio
from botocore.exceptions import ClientError
from fastapi import APIRouter

from core.data.s3_storage import S3Dep
from core.schemas.chat_schema import WSPingS3Schema

router = APIRouter(prefix='/api/public')



@router.post('/s3/long_ping')
async def wait_for_object(ping_sch: WSPingS3Schema, s3: S3Dep):
    elapsed = 0
    while elapsed < ping_sch.timeout:
        try:
            await s3.head_object(Bucket=s3.bucket, Key=ping_sch.key)
            return {'success': True, 'message': 'Объект в С3'}
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                await asyncio.sleep(ping_sch.interval)
                elapsed += ping_sch.interval
            else:
                raise e
    return {'success': False, 'message': 'Объект не сохранился в С3, Таймаут'}
