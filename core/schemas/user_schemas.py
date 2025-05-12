from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field
from pydantic import EmailStr

from core.utils.passw_validate import validate_password


class UserBase(BaseModel):
    id: int = 1


class UserDBSchema(BaseModel):
    email: EmailStr


class UserLogInSchema(UserDBSchema):
    passw: str

class UserRegSchema(UserDBSchema):
    passw: Annotated[str, BeforeValidator(validate_password)]
    name: Annotated[str| None, Field(default='Пользователь Pied Market')]