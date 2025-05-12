from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException, Response

from core.db_data.postgre import PgSqlDep
from core.utils.processing_data.jwt_utils.jwt_encode_decode import get_jwt_decode_payload, set_jwt_encode
from core.utils.processing_data.jwt_utils.to_overhead_format import add_ttl_limit


async def release_tokens(db: PgSqlDep, id: int):
    session_id = str(uuid4());print(session_id)

    access_token = add_ttl_limit({
        'sub': str(id),
        's_id': session_id
    })
    refresh_token = add_ttl_limit({'sub': str(id)}, True)

    encoded_aT, encoded_rT = set_jwt_encode(access_token), set_jwt_encode(refresh_token)
    await db.make_session(session_id, id, refresh_token['iat'], refresh_token['exp'], encoded_rT)

    return encoded_aT, encoded_rT


def check_token(access_token: str, refresh_token: str):
    payload_aT, payload_rT = get_jwt_decode_payload(access_token), get_jwt_decode_payload(refresh_token)
    now = datetime.utcnow()

    if payload_aT['exp'] < now:
        # обращаемся к rT
        if payload_rT['exp'] < now:
            raise HTTPException(status_code=401, detail='нужна повторная аутентификация')

        # if encryption.verify(refresh_token, )
        #     pass

    return payload_aT