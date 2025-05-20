from fastapi import APIRouter, Response, Request, HTTPException

from core.config_dir.debug_logger import log_debug
from core.data.postgre import PgSqlDep
from core.utils.processing_data.jwt_processing import issue_aT_rT
from core.schemas.user_schemas import UserRegSchema, UserLogInSchema, TokenPayloadSchema
from core.config_dir.config import encryption
from core.config_dir.logger import log_event
from core.utils.anything import Tags, Events, hide_log_param

router = APIRouter(prefix='/api/users', tags=[Tags.users])



@router.post('/sign_up', summary="Регистрация")
async def registration_user(creds: UserRegSchema, db: PgSqlDep, request: Request):
    insert_attempt = await db.users.reg_user(creds.email, creds.passw, creds.name)

    if insert_attempt == 'INSERT 0 0':
        log_event(Events.unluck_registr_user, request, status=409, name=creds.name, email=hide_log_param(creds.email), level='WARNING')
        raise HTTPException(status_code=409, detail='Пользователь уже существует')
    log_event(Events.registr_user, request, status=200, name=creds.name, email=hide_log_param(creds.email))
    return {'success': True, 'message': 'Пользователь добавлен'}


@router.post('/login', summary="Вход в аккаунт")
async def log_in(creds: UserLogInSchema, response: Response, db: PgSqlDep, request: Request):
    db_user = await db.users.select_user(creds.email)

    if db_user and encryption.verify(creds.passw, db_user['passw']):
        token_schema = TokenPayloadSchema(
            id=db_user['id'],
            user_agent=request.headers['user-agent'],
            ip=request.client.host
        )
        access_token, refresh_token = await issue_aT_rT(db,token_schema)

        response.set_cookie('access_token', access_token, httponly=True)
        response.set_cookie('refresh_token', refresh_token, httponly=True)
        return {'success': True, 'message': 'Куки у Юзера'}
    log_event(Events.unluck_login_user, request, status=401, email=hide_log_param(creds.email), level='WARNING')
    raise HTTPException(status_code=401, detail='Неверный логин или пароль')


@router.post('/profile/seances', summary='Все Устройства аккаунта')
async def show_seances(request: Request, db: PgSqlDep):
    seances = await db.auth.all_seances_user(request.state.user_id, request.state.session_id)
    return {'seances': seances}




@router.get('/log_checker')
async def generate_log(request: Request):
    log_event(Events.TEST, request, email='epic', status=200, user_id=123)
    log_event(Events.TEST, request, level='WARNING', status=304)
    log_event(Events.TEST, request, level='ERROR', status=404)
    log_event(Events.TEST, request, level='CRITICAL', status=500)
    return {'success': True, 'message': 'time to logs!'}













