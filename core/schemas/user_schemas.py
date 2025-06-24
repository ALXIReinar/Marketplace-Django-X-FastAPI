import re

from typing import Annotated


from pydantic import BaseModel, Field, field_validator
from pydantic import EmailStr
from typing_extensions import Literal


class ValidatePasswSchema(BaseModel):
    passw: str
    @field_validator('passw', check_fields=False)
    def validate_password(cls, value) -> bytes:
        passw = value.strip()
        if len(passw) < 8:
            raise ValueError('String shorter 8 characters')

        spec_spell = digit = uppercase = False

        for ch in passw:
            if re.match(r'[А-Яа-я]', ch):
                raise ValueError('Password must consist of English chars only')
            if ch == ' ':
                raise ValueError('Password must not contain spaces')

            if ch.isdigit():
                digit = True
            elif ch in {'.', ';', '\\', '!', '_', '/', '&', ')', '>', '$', '*', '}', '=', ',', '[', '#', '%', '~', ':',
                        '{',
                        ']', '?', '@', "'", '(', '`', '"', '^', '|', '<', '-', '+'}:
                spec_spell = True
            elif ch == ch.upper():
                uppercase = True

        if spec_spell and digit and uppercase:
            return passw.encode()
        raise ValueError('Password does not match the conditions: 1 Spec char, 1 digit, 1 Uppercase letter')

class UpdatePasswSchema(ValidatePasswSchema):
    reset_token: str

class UserLogInSchema(BaseModel):
    email: EmailStr
    passw: str

class UserRegSchema(ValidatePasswSchema):
    email: EmailStr
    name: Annotated[str | None, Field(default='Пользователь Pied Market')]

class RecoveryPasswSchema(BaseModel):
    email: EmailStr


class TokenPayloadSchema(BaseModel):
    id: int
    user_agent: str = Field(max_length=512)
    ip: str = Field(max_length=39)

class RecoveryPrepareSchema(RecoveryPasswSchema):
    user: dict
    reset_token: str