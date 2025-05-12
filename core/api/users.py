from fastapi import APIRouter, Response, HTTPException

from core.config_dir.config import encryption
from core.config_dir.logger import Tags
from core.db_data.postgre import PgSqlDep
from core.schemas.user_schemas import UserRegSchema, UserLogInSchema
from core.utils.processing_data.jwt_processing import release_tokens

router = APIRouter(prefix='/api/users')



@router.post('/sign_up', tags=[Tags.users], summary="Регистрация")
async def registration_user(creds: UserRegSchema, db: PgSqlDep):
    insert_attempt = await db.reg_user(creds.email, creds.passw, creds.name)

    if insert_attempt == 'INSERT 0 0':
        raise HTTPException(status_code=409, detail='Пользователь уже существует')
    return {'success': True, 'message': 'Пользователь добавлен'}


@router.post('/login', tags=[Tags.users], summary="Вход в аккаунт")
async def log_in(creds: UserLogInSchema, response: Response, db: PgSqlDep):
    db_user = await db.select_user(creds.email)

    if db_user and encryption.verify(creds.passw, db_user['passw']):
        access_token, refresh_token = await release_tokens(db, id=db_user['id'])

        response.set_cookie('access_token', access_token, httponly=True)
        response.set_cookie('refresh_token', refresh_token, httponly=True)
        return {'success': True, 'message': 'Куки у Юзера'}

    raise HTTPException(status_code=401, detail='Неверный логин или пароль')


