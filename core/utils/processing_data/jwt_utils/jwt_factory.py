from datetime import datetime

from core.config_dir.config import encryption, env
from core.data.postgre import PgSqlDep
from core.schemas.user_schemas import TokenPayloadSchema
from core.utils.anything import token_types, TokenTypes
from core.utils.processing_data.jwt_utils.jwt_encode_decode import set_jwt_encode


def add_ttl_limit(data: dict, token_ttl: str):
    created_at = datetime.utcnow()

    ttl = env.JWTs.ttl_aT
    if token_types[token_ttl] == TokenTypes.refresh_token:
        ttl = env.JWTs.ttl_rT
    elif token_types[token_ttl] == TokenTypes.ws_token:
        ttl = env.JWTs.ttl_wT
    expired_at = created_at + ttl

    data.update(
        iat=created_at,
        exp=expired_at
    )
    return data


async def issue_token(
        payload: dict,
        token: TokenTypes | str,
        db: PgSqlDep = None,
        session_id: str | None=None,
        client: TokenPayloadSchema=None
):
    if token_types[token] == TokenTypes.refresh_token:
        rT = add_ttl_limit(payload, token)
        encoded_rT = set_jwt_encode(rT)
        hashed_rT = encryption.hash(encoded_rT)
        await db.auth.make_session(session_id, int(payload['sub']), rT['iat'], rT['exp'], client.user_agent, client.ip, hashed_rT)
        return hashed_rT
    elif token_types[token] == TokenTypes.access_token:
        payload['s_id'] = session_id if not payload.get('s_id') else payload['s_id']
        aT = add_ttl_limit(payload, token)
        return set_jwt_encode(aT)
    wT = add_ttl_limit(payload, token)
    return set_jwt_encode(wT)
