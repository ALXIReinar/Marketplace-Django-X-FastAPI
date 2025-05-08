from pydantic import BaseModel, Field
from typing_extensions import Optional


class UserBase(BaseModel):
    id: int

