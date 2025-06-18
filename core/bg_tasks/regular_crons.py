from core.config_dir.logger import log_event
from core.data.postgre import init_pool, set_connection, PgSql
from core.utils.anything import Events


async def flush_expired_rT():
    log_event(Events.periodic_cron + 'Очистка рефреш_токенов', level='WARNING')
    pool = await set_connection()
    async with pool.acquire() as conn:
        db = PgSql(conn)
        await db.chats.remove_rubbish_messages()
    log_event(Events.cron_completed + "Истёкшие сессии удалены", level='WARNING')


async def clear_trash_messages():
    log_event(Events.periodic_cron + "Висячие сообщения удаляются", level='WARNING')
    async with init_pool() as db:
        await db.auth.slam_refresh_tokens()
    log_event(Events.cron_completed + "Мусорные сообщения удалены!", level='WARNING')