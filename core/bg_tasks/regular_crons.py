from fastapi import APIRouter
from starlette.requests import Request

from core.config_dir.logger import log_event
from core.data.postgre import PgSqlDep
from core.utils.anything import Events, Tags

router = APIRouter(prefix='/api/bg_tasks/crons', tags=[Tags.crons])



@router.delete('/flush_refresh-tokens')
async def flush_expired_rT(request: Request, db: PgSqlDep):
    log_event(Events.periodic_cron + 'Очистка рефреш_токенов', request=request, level='WARNING')
    await db.chats.remove_rubbish_messages()
    log_event(Events.cron_completed + "Истёкшие сессии удалены", request=request, level='WARNING')

@router.delete('/delete_chat-messages')
async def clear_trash_messages(request: Request, db: PgSqlDep):
    log_event(Events.periodic_cron + "Висячие сообщения удаляются", request=request, level='WARNING')
    await db.auth.slam_refresh_tokens()
    log_event(Events.cron_completed + "Мусорные сообщения удалены!", request=request, level='WARNING')
