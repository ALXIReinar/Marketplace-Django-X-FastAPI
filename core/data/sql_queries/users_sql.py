from collections import namedtuple

from asyncpg import Connection
from pydantic import EmailStr

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


class ChatQueries:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_user_chats(self, user_id: int, limit: int, offset: int):
        query = '''
<<<<<<< HEAD
        
        WITH last_msg AS ( 
        SELECT DISTINCT ON (chat_id) chat_id, owner_id, text_field, type, writed_at
        FROM chat_messages
        WHERE chat_id IN (
            SELECT chat_id FROM chat_users WHERE user_id = $1
        )
        ORDER BY chat_id, writed_at DESC
=======
        WITH last_msg AS (
            SELECT DISTINCT ON (chat_id) chat_id, owner_id, text_field, type, writed_at
            FROM chat_messages
            WHERE chat_id IN (
                SELECT chat_id FROM chat_users WHERE user_id = $1
            )
            ORDER BY chat_id, writed_at DESC
>>>>>>> cbe7169 (проработка вебсокета по части БД, ручка на поднятие индекса в ЕС)
        )
        SELECT c_u.chat_id, c_u.chat_name, c_u.chat_img, l.text_field, l.type, l.writed_at, c_u.notif_mode,
          COUNT(m.id) FILTER (WHERE m.local_id > COALESCE(r.last_read_local_id, 0)) AS unread_count
        FROM chat_users c_u
        JOIN last_msg l ON c_u.chat_id = l.chat_id
        LEFT JOIN readed_mes r ON r.chat_id = c_u.chat_id AND r.user_id = c_u.user_id
        LEFT JOIN chat_messages m ON m.chat_id = c_u.chat_id
        WHERE c_u.user_id = $1 AND c_u.state BETWEEN 1 AND 2
        GROUP BY c_u.chat_id, c_u.chat_name, c_u.chat_img, l.text_field, l.type, l.writed_at, c_u.notif_mode, r.last_read_local_id
        ORDER BY l.writed_at DESC
<<<<<<< HEAD
        LIMIT $2 OFFSET $3
        '''
        chat_records = await self.conn.fetch(query, user_id, limit, offset)
        return chat_records

    async def save_message(
            self,
            chat_id: int,
            user_id: int,
            msg_type: str,
            text_field: str | None = None,
            reply_id: int | None = None
    ):
        query = '''
        INSERT INTO chat_messages (chat_id , owner_id, text_field, type, reply_id, local_id)
        VALUES($1, $2, $3, $4, $5,(SELECT COALESCE(MAX(local_id), 0) + 1 FROM chat_messages WHERE chat_id = $1))
        RETURNING local_id
        '''
        local_id = await self.conn.execute(query, chat_id, user_id, text_field, msg_type, reply_id)
        return local_id
=======
        LIMIT $2 OFFSET $3;
        '''
        chat_records = await self.conn.fetch(query, user_id, limit, offset)
        return chat_records
>>>>>>> cbe7169 (проработка вебсокета по части БД, ручка на поднятие индекса в ЕС)
