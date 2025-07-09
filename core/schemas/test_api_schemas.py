from typing_extensions import Literal, Annotated
from pydantic import BaseModel, Field


class DBTestNeeds(BaseModel):
    query: str
    method: Literal['exe', 'fetch', 'fetchrow']
    args: Annotated[list | None, Field(default=[])]
