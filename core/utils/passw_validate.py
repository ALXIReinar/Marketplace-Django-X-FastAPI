import re

from pydantic import ValidationError


def validate_password(passw: str) -> bytes:
    passw = passw.strip()
    if len(passw) < 8:
        raise ValidationError('String shorter 8 characters')

    spec_spell = digit = uppercase = False

    for ch in passw:
        if re.match(r'[А-Яа-я]', ch):
            raise ValidationError('Password must consist of English chars only')
        if ch == ' ':
            raise ValidationError('Password must not contain spaces')

        if ch.isdigit():
            digit = True
        elif ch in {'.', ';', '\\', '!', '_', '/', '&', ')', '>', '$', '*', '}', '=', ',', '[', '#', '%', '~', ':', '{',
                    ']', '?', '@', "'", '(', '`', '"', '^', '|', '<', '-', '+'}:
            spec_spell = True
        elif ch == ch.upper():
            uppercase = True

    if spec_spell and digit and uppercase:
        return passw.encode()
    raise ValidationError('Password does not match the conditions: 1 Spec char, 1 digit, 1 uppercase letter')
