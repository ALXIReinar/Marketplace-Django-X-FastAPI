from asyncpg import Connection
from pydantic import EmailStr

from core.config_dir.config import encryption


class UsersQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def reg_user(self, email, passw: str):
        query = 'INSERT INTO users (email, passw) VALUES($1, $2) ON CONFLICT (email) DO NOTHING RETURNING id'
        hashed = encryption.hash(passw)

        res = await self.conn.execute(query, email, hashed)
        return res

    async def select_user(self, email):
        query = 'SELECT id, passw FROM users WHERE email = $1'
        res = await self.conn.fetchrow(query, email)
        return res

    async def get_id_name_by_email(self, email: EmailStr):
        query = 'SELECT id, name FROM users WHERE email = $1'
        return await self.conn.fetchrow(query, email)

    async def set_new_passw(self, user_id: int, passw: str):
        query = 'UPDATE users SET passw = $1 WHERE id = $2'
        await self.conn.execute(query, passw, user_id)



class AuthQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def make_session(
            self,
            session_id: str,
            user_id: int,
            iat: int,
            exp: int,
            user_agent: str,
            ip: str,
            hashed_rT: str
    ):
        query = '''
        INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT (session_id) DO UPDATE SET  iat = $3, exp = $4, refresh_token = $5, ip = $7
        '''
        await self.conn.execute(query, session_id, user_id, iat, exp, hashed_rT, user_agent, ip)


    async def get_actual_rt(self, user_id: int, session_id: str):
        query = '''SELECT refresh_token FROM sessions_users
                   WHERE user_id = $1 AND session_id = $2 AND "exp" > now()'''
        res = await self.conn.fetchrow(query, user_id, session_id)
        return res


    async def all_seances_user(self, user_id: int, session_id: str):
        query = 'SELECT user_agent, ip FROM sessions_users WHERE user_id = $1 AND session_id = $2'
        res = await self.conn.fetch(query, user_id, session_id)
        return res

    async def check_exist_session(self, user_id: int, user_agent: str):
        query = '''
        SELECT session_id FROM public.sessions_users WHERE user_id = $1 AND user_agent = $2
        '''
        res = await self.conn.fetchrow(query, user_id, user_agent)
        return res

    async def session_termination(self, user_id: int, session_id: str):
        query = 'DELETE FROM sessions_users WHERE user_id = $1 AND session_id = $2'
        await self.conn.execute(query, user_id, session_id)


    async def slam_refresh_tokens(self):
        query = 'DELETE FROM sessions_users WHERE exp < now()'
        await self.conn.execute(query)