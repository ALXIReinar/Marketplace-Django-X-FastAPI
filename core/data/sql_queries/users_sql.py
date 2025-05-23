from asyncpg import Connection

from core.config_dir.config import encryption


class UsersQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def reg_user(self, email, passw: str, name: str):
        query = 'INSERT INTO users (email, passw, name) VALUES($1, $2, $3) ON CONFLICT (email) DO NOTHING RETURNING id'
        hashed = encryption.hash(passw)

        res = await self.conn.execute(query, email, hashed, name)
        return res

    async def select_user(self, email):
        query = 'SELECT id, passw FROM users WHERE email = $1'
        res = await self.conn.fetchrow(query, email)
        return res



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
        query = 'INSERT INTO sessions_users (session_id, user_id, iat, exp, refresh_token, user_agent, ip) VALUES($1,$2,$3,$4,$5,$6,$7)'
        await self.conn.execute(query, session_id, user_id, iat, exp, hashed_rT, user_agent, ip)


    async def get_actual_rt(self, user_id: int, session_id: str):
        query = '''SELECT refresh_token, seance FROM sessions_users
                   WHERE user_id = $1 AND session_id = $2 AND "exp" > now()'''
        res = await self.conn.fetchrow(query, user_id, session_id)
        return res

    async def all_seances_user(self, user_id: int, session_id: str):
        query = 'SELECT user_agent, ip FROM sessions_users WHERE user_id = $1 AND session_id = $2'
        res = await self.conn.fetch(query, user_id, session_id)
        return res
