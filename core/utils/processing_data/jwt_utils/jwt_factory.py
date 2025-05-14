from collections import namedtuple
from datetime import datetime
from uuid import uuid4

from core.config_dir.config import get_env_vars, encryption
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import TokenPayloadSchema
from core.utils.processing_data.jwt_utils.jwt_encode_decode import set_jwt_encode


def add_ttl_limit(data: dict, long_ttl: bool=False):
    created_at = datetime.utcnow()

    ttl = get_env_vars().JWTs.ttl_aT
    if long_ttl:
        ttl = get_env_vars().JWTs.ttl_rT
    expired_at = created_at + ttl

    data.update(
        iat=created_at,
        exp=expired_at
    )
    return data


async def issue_token(
        db: PgSqlDep,
        payload: dict,
        session_id: str | None=None,
        client: TokenPayloadSchema=None,
        refresh_token: bool=False
):
    if refresh_token:
        rT = add_ttl_limit(payload, True)
        encoded_rT = set_jwt_encode(rT)
        hashed_rT = encryption.hash(encoded_rT)
        await db.make_session(session_id, int(payload['sub']), rT['iat'], rT['exp'], client.user_agent, client.ip, hashed_rT)
        return hashed_rT

    payload['s_id'] = session_id if not payload.get('s_id') else payload['s_id']
    aT = add_ttl_limit(payload)
    return set_jwt_encode(aT)