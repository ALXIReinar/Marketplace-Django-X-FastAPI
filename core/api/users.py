from fastapi import APIRouter, Response, Request, HTTPException

from core.config_dir.config import encryption
from core.config_dir.logger import Tags
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import UserRegSchema, UserLogInSchema, TokenPayloadSchema
from core.utils.processing_data.jwt_processing import issue_aT_rT

router = APIRouter(prefix='/api/users')



@router.post('/sign_up', tags=[Tags.users], summary="Регистрация")
async def registration_user(creds: UserRegSchema, db: PgSqlDep):
    insert_attempt = await db.reg_user(creds.email, creds.passw, creds.name)

    if insert_attempt == 'INSERT 0 0':
        raise HTTPException(status_code=409, detail='Пользователь уже существует')
    return {'success': True, 'message': 'Пользователь добавлен'}


@router.post('/login', tags=[Tags.users], summary="Вход в аккаунт")
async def log_in(creds: UserLogInSchema, response: Response, db: PgSqlDep, request: Request):
    db_user = await db.select_user(creds.email)

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

    raise HTTPException(status_code=401, detail='Неверный логин или пароль')


@router.post('/profile/seances')
async def show_seances(request: Request, db: PgSqlDep):
    seances = await db.all_seances_user(request.state.user_id, request.state.session_id)
    return {'seances': seances}



















