from typing import Annotated

from aiobotocore.session import ClientCreatorContext
from fastapi.params import Depends

from core.config_dir.config import cloud_session, get_env_vars


class S3Storage:
    def __init__(
            self,
            cloud_session: ClientCreatorContext,
            bucket_name,
    ):
        self.bucket = bucket_name
        self.session = cloud_session


    async def save_file(self, file_path, bucket=None):
        if not bucket: bucket = self.bucket

        with open(file_path, 'rb') as file:
            await self.session.put_object(
                Bucket=bucket,
                Key=file_path,
                Body=file
            )


async def set_cloud_session():
    async with cloud_session() as cloud:
        yield S3Storage(cloud, get_env_vars().s3_bucket_name)

S3Dep = Annotated[S3Storage, Depends(set_cloud_session)]
