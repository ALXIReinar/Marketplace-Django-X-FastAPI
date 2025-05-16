import secrets
from uuid import uuid4

from fastapi import Request

from core.config_dir.config import encryption
from core.config_dir.logger import log_event
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import TokenPayloadSchema
from core.utils.anything import Events
from core.utils.processing_data.jwt_utils.jwt_factory import issue_token


async def issue_aT_rT(db: PgSqlDep, token_schema: TokenPayloadSchema):
    session_id = str(uuid4())
    frame_token = {
        'sub': str(token_schema.id),
    }
    hashed_rT = encryption.hash(await issue_token(db, frame_token, session_id=session_id, client=token_schema, refresh_token=True))
    encoded_aT = await issue_token(db, frame_token, session_id=session_id)
    return encoded_aT, hashed_rT


async def reissue_aT(access_token: dict, refresh_token: str, db: PgSqlDep, request: Request):
    sub, s_id = access_token['sub'], access_token['s_id']
    db_rT = await db.get_actual_rt(int(sub), access_token['s_id'])

    if db_rT and (db_rT['seance'] and secrets.compare_digest(db_rT['refresh_token'], refresh_token)):
        # рефреш_токен СОВПАЛ с выданным и ещё НЕ ИСТЁК
        log_event(Events.new_aT, request, s_id=s_id, user_id=sub)
        new_access_token = issue_token(db, {'sub': sub, 's_id': s_id})
        return new_access_token

    if not db_rT['seance']:
        log_event(Events.fake_rT_or_exp, request, s_id=s_id, user_id=sub, level="CRITICAL")
    # рефреш_токен ИСТЁК / НЕ СОВПАЛ / ОТОЗВАН
    return 401