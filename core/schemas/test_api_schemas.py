from typing_extensions import Literal, Annotated
from pydantic import BaseModel, Field


class DBTestNeeds(BaseModel):
    query: str
    method: Literal['exe', 'fetch', 'fetchrow']
    args: Annotated[list | None, Field(default=[])]

class WSPingS3Schema(BaseModel):
    key: str
    timeout: float = Field(default=120.0)
    interval: float = Field(default=45.0)