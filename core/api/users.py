import secrets
from uuid import uuid4

from fastapi import APIRouter, Response, Request, HTTPException
from starlette.responses import JSONResponse

from core.bg_tasks.celery_processing import sending_email_code
from core.data.postgre import PgSqlDep
from core.data.redis_storage import RedisDep
from core.utils.processing_data.jwt_processing import issue_aT_rT
from core.schemas.user_schemas import UserRegSchema, UserLogInSchema, TokenPayloadSchema, UpdatePasswSchema, RecoveryPasswSchema
from core.config_dir.config import encryption
from core.config_dir.logger import log_event
from core.utils.anything import Tags, Events, hide_log_param

router = APIRouter(prefix='/api/users', tags=[Tags.users])



@router.post('/sign_up', summary="Регистрация")
async def registration_user(creds: UserRegSchema, db: PgSqlDep, request: Request):
    insert_attempt = await db.users.reg_user(creds.email, creds.passw, creds.name)
    if insert_attempt == 'INSERT 0 0':
        log_event(Events.unluck_registr_user + f" name: {creds.name}; email: {hide_log_param(creds.email)}", request=request, level='WARNING')
        raise HTTPException(status_code=409, detail='Пользователь уже существует')
    log_event(Events.registr_user + f" name: {creds.name}, email: {hide_log_param(creds.email)}", request=request)
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
        log_event("Пользователь Вошёл в акк | user_id: %s", db_user['id'], request=request, level='INFO')
        return {'success': True, 'message': 'Куки у Юзера'}
    log_event(Events.unluck_login_user + f" email: {hide_log_param(creds.email)}", request=request, level='WARNING')
    raise HTTPException(status_code=401, detail='Неверный логин или пароль')


@router.put('/logout')
async def log_out(request: Request, response: Response):
    response.delete_cookie('access_token')
    # response.delete_cookie('refresh_token')
    log_event("Пользователь разлогинился | user_id: %s; s_id: %s", request.state.user_id, request.state.session_id, request=request)
    return {'success': True, 'message': 'Пользователь вне аккаунта'}

@router.post('/profile/seances', summary='Все Устройства аккаунта')
async def show_seances(request: Request, db: PgSqlDep):
    log_event("Запрос всех Устройств с акка | user_id: %s; s_id: %s", request.state.user_id, request.state.session_id, request=request, level='INFO')
    seances = await db.auth.all_seances_user(request.state.user_id, request.state.session_id)
    return {'seances': seances}



"Сброс Пароля"
@router.post('/passw/forget_passw')
async def account_recovery(email: RecoveryPasswSchema, db: PgSqlDep, request: Request):
    log_event('Попытка сброса пароля | email: %s', hide_log_param(email.email), request=request, level='WARNING')

    user = await db.users.get_id_name_by_email(email.email)
    reset_token = str(uuid4())
    sending_email_code.apply_async(args=[email.email, user, reset_token])

    return JSONResponse(status_code=200, content={
        'reset_token': reset_token,
        'message': 'Письмо с кодом подтверждения было отправлено!'
    })


@router.get('/passw/compare_confirm_code')
async def compare_mail_user_code(reset_token: str, code: str, request: Request, redis: RedisDep):
    pre_user_id = await redis.get(reset_token)
    if pre_user_id:
        "На случай, если вернутся на страницу назад, а в кэш-попадание уже было"
        user_id = pre_user_id.decode()
        server_code = await redis.get(user_id)
        if server_code and secrets.compare_digest(server_code, code.encode()):
            await redis.delete(user_id)
            return {'success': True, 'message': 'Коды совпали, можно менять пароль'}
        log_event("Код пользователя и код на сервере не совпали! | user_id: %s", user_id, request=request, level='WARNING')
        raise HTTPException(status_code=422, detail='Код неверный')
    log_event("Кто-то решил поиграться, или вернуться на прошлую страницу | reset_token: %s", reset_token, request=request, level='CRITICAL')
    raise HTTPException(status_code=410, detail='Сессия истекла, повторите процедуру')


@router.put('/passw/set_new_passw')
async def reset_password(
        update_secrets: UpdatePasswSchema,
        db: PgSqlDep,
        response: Response,
        request: Request,
        redis: RedisDep
):
    user_id = await redis.get(update_secrets.reset_token)
    if user_id:
        await redis.delete(update_secrets.reset_token)

        hashed_passw = encryption.hash(update_secrets.passw)
        await db.users.set_new_passw(int(user_id.decode()), hashed_passw)
        log_event("Юзер сменил Пароль | user_id: %s", user_id, request=request, level='WARNING')
        return {'success': True, 'message': 'Пароль обновлён!'}
    log_event("Кто-то решил поиграться, или вернуться на прошлую страницу; код истёк | reset_token: %s", update_secrets.reset_token, request=request, level='CRITICAL')
    raise HTTPException(410, detail='Сессия утрачена. Повторите процедуру')