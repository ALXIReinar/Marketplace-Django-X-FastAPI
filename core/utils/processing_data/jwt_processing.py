import secrets
from uuid import uuid4

from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.schemas.user_schemas import TokenPayloadSchema
from core.utils.anything import Events
from core.utils.processing_data.jwt_utils.jwt_factory import issue_token


async def issue_aT_rT(db: PgSqlDep, token_schema: TokenPayloadSchema):
    session_id = await db.auth.check_exist_session(token_schema.id, token_schema.user_agent)
    if session_id:
        session_id = session_id['session_id']
        log_event('Существующая сессия: user_id: %s; s_id: %s; ip: %s', token_schema.id, session_id, token_schema.ip)
    else:
        session_id = str(uuid4())
        log_event('Новая сессия | user_id: %s; user_agent: %s; ip: %s',
                  token_schema.id, token_schema.user_agent, token_schema.ip)


    frame_token = {
        'sub': str(token_schema.id),
    }
    hashed_rT = await issue_token(frame_token, 'refresh_token', db=db, session_id=session_id, client=token_schema)
    encoded_aT = await issue_token(frame_token, 'access_token', session_id=session_id)
    return encoded_aT, hashed_rT


async def reissue_aT(access_token: dict, refresh_token: str, db: PgSqlDep):
    sub, s_id = access_token['sub'], access_token['s_id']
    db_rT = await db.auth.get_actual_rt(int(sub), access_token['s_id'])

    if db_rT and secrets.compare_digest(db_rT['refresh_token'], refresh_token):
        # рефреш_токен СОВПАЛ с выданным и ещё НЕ ИСТЁК
        log_event(Events.new_aT + f" | s_id: {s_id}; user_id: {sub}")
        new_access_token = await issue_token({'sub': sub, 's_id': s_id}, 'access_token')
        return new_access_token

    if db_rT is None:
        log_event(Events.fake_rT_or_exp+ f"s_id: {s_id}; user_id: {sub}", level="CRITICAL")
    # рефреш_токен ИСТЁК / НЕ СОВПАЛ / ОТОЗВАН
    return 401