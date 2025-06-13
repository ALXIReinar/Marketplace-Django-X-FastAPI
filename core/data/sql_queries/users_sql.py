from asyncpg import Connection
from pydantic import EmailStr

from core.config_dir.config import encryption
from asyncpg.exceptions import UniqueViolationError

from core.config_dir.logger import log_event


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
        query = '''SELECT refresh_token FROM sessions_users
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
        WITH last_msg AS ( 
        SELECT DISTINCT ON (chat_id) chat_id, owner_id, text_field, type, writed_at
        FROM chat_messages
        WHERE chat_id IN (
            SELECT chat_id FROM chat_users WHERE user_id = $1
        )
        ORDER BY chat_id, writed_at DESC
        )
        SELECT c_u.chat_id, c_u.chat_name, c_u.chat_img, l.text_field, l.type, l.writed_at, c_u.notif_mode,
          CASE WHEN l.owner_id = $1 THEN TRUE ELSE FALSE END AS is_me, 
          COUNT(m.id) FILTER (WHERE m.local_id > COALESCE(r.last_read_local_id, 0)) AS unread_count
        FROM chat_users c_u
        JOIN last_msg l ON c_u.chat_id = l.chat_id
        LEFT JOIN readed_mes r ON r.chat_id = c_u.chat_id AND r.user_id = c_u.user_id
        LEFT JOIN chat_messages m ON m.chat_id = c_u.chat_id
        WHERE c_u.user_id = $1 AND c_u.state BETWEEN 1 AND 2
        GROUP BY c_u.chat_id, c_u.chat_name, c_u.chat_img, l.text_field, l.type, l.writed_at, c_u.notif_mode, is_me
        ORDER BY l.writed_at DESC
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
            reply_id: int | None = None,
            attempt_again: int = 0
    ):
        if attempt_again >= 2:
            return {'success': False, 'msg_id': -1}
        query_last_local_id  = '''SELECT (COALESCE(MAX(local_id), 0) + 1) AS next_local_id FROM chat_messages WHERE chat_id = $1'''
        query_commit_transaction = '''
        INSERT INTO chat_messages (chat_id , owner_id, text_field, type, reply_id, local_id) VALUES($1,$2,$3,$4,$5,$6);
        '''
        try:
            "Начало транзакции"
            await self.conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED')

            local_id = (await self.conn.fetchrow(query_last_local_id, chat_id))['next_local_id']
            await self.conn.execute(
                query_commit_transaction,
                chat_id, user_id, text_field, msg_type, reply_id, local_id
            )

            "Коммит Транзакции"
            await self.conn.execute('COMMIT')
        except UniqueViolationError:
            "Завершаем транзакцию Либо ловим Конкурентный Доступ"
            await self.conn.execute('ROLLBACK')
            log_event("Идём на %s круг, msg_package: %s", attempt_again, (chat_id, user_id, text_field, msg_type, reply_id), level='WARNING')
            local_id = await self.save_message(chat_id, user_id, msg_type, text_field, reply_id, attempt_again=attempt_again + 1)

        return {'success': True, 'msg_id': local_id, 'user_id': user_id}

    async def get_chat_messages(self, chat_id: int, limit: int, offset: int):
        query = '''
        SELECT owner_id, text_field, content_path, type, writed_at, reply_id, local_id FROM chat_messages
        WHERE chat_id = $1
        LIMIT $2 OFFSET $3
        '''
        res = await self.conn.fetch(query, chat_id, limit, offset)
        return res