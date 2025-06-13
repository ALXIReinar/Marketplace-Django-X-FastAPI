import jwt

from typing import Any

from jwt import DecodeError, ExpiredSignatureError

from core.config_dir.config import get_env_vars


def set_jwt_encode(payload: dict[str, Any]):
    encoded = jwt.encode(
        payload=payload,
        key=get_env_vars().JWTs.private_key.read_text(),
        algorithm=get_env_vars().JWTs.algorithm
    )
    return encoded

def get_jwt_decode_payload(encoded_jwt: str, verify_exp: bool=False):
    try:
        decoded = jwt.decode(
            jwt=encoded_jwt,
            key=get_env_vars().JWTs.public_key.read_text(),
            algorithms=[get_env_vars().JWTs.algorithm],
            options={'verify_exp': verify_exp}
        )
    except DecodeError:
        decoded = 401
    except ExpiredSignatureError:
        decoded = 401
    return decoded
