from asyncpg import Connection, UniqueViolationError

from core.config_dir.config import env
from core.config_dir.logger import log_event


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
            content_path: str | None = None,
            reply_id: int | None = None,
            attempt_again: int = 0
    ):
        if attempt_again >= 2:
            return {'success': False, 'msg_id': -1}
        query_last_local_id  = '''SELECT (COALESCE(MAX(local_id), 0) + 1) AS next_local_id FROM chat_messages WHERE chat_id = $1'''
        query_commit_transaction = '''
        INSERT INTO chat_messages (chat_id , owner_id, text_field, content_path, type, reply_id, local_id) VALUES($1,$2,$3,$4,$5,$6,$7);
        '''
        try:
            "Начало транзакции"
            await self.conn.execute('BEGIN ISOLATION LEVEL READ COMMITTED')

            local_id = (await self.conn.fetchrow(query_last_local_id, chat_id))['next_local_id']
            await self.conn.execute(
                query_commit_transaction,
                chat_id, user_id, text_field, content_path, msg_type, reply_id, local_id
            )

            "Коммит Транзакции"
            await self.conn.execute('COMMIT')
        except UniqueViolationError:
            "Завершаем транзакцию Либо ловим Конкурентный Доступ"
            await self.conn.execute('ROLLBACK')
            log_event("Идём на %s круг, msg_package: %s", attempt_again, (chat_id, user_id, text_field, content_path, msg_type, reply_id), level='WARNING')
            local_id = await self.save_message(chat_id, user_id, msg_type, text_field, reply_id, attempt_again=attempt_again + 1)

        return {'success': True, 'msg_id': local_id, 'user_id': user_id}

    async def get_chat_messages(self, chat_id: int, limit: int, offset: int, user_id: int | None = None):
        sub_query_for_tp_on_edge_mes = f'''
        AND c_m.local_id > (SELECT COALESCE(last_read_local_id, 0) FROM readed_mes WHERE chat_id = $1 AND user_id = $4) - {env.delta_layout_msg}'''
        query = '''
        SELECT c_m.owner_id, c_u.chat_img, c_m.text_field, c_m.content_path, c_m.type, c_m.writed_at, c_m.reply_id, c_m.local_id FROM chat_messages c_m
        JOIN chat_users c_u ON c_u.chat_id = c_m.chat_id AND c_u.user_id = c_m.owner_id
        WHERE c_m.chat_id = $1 {}
        ORDER BY c_m.local_id DESC
        LIMIT $2 OFFSET $3
        '''
        if user_id is None:
            res = await self.conn.fetch(query.format(''), chat_id, limit, offset)
            log_event(query.format(''), level='DEBUG')
        else:
            res = await self.conn.fetch(query.format(sub_query_for_tp_on_edge_mes), chat_id, limit, offset, user_id)
        return res


    async def update_readed_messages(self, user_id: int, chat_id: int, local_mes_id: int):
        query = '''
        INSERT INTO readed_mes (user_id, chat_id, last_read_local_id) VALUES($1,$2,$3)
        ON CONFLICT (user_id, chat_id) DO UPDATE SET last_read_local_id = $3
        '''
        await self.conn.execute(query, user_id, chat_id, local_mes_id)