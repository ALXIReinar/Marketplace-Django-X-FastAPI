from fastapi import APIRouter
from starlette.requests import Request

from core.config_dir.base_dependencies import PagenChatDep
from core.data.postgre import PgSqlDep
from core.utils.anything import Tags

router = APIRouter(prefix='/api/chats', tags=[Tags.chat])



@router.get('/')
async def get_chats(pagen: PagenChatDep, request: Request, db: PgSqlDep):
    """
    state sheets:
    - 0 - deleted
    - 1 - active
    - 2 - blocked

    chat_messages:
     - type: 1 - text
             2 - media
             3 - audio
    """
    user_id = request.user.id
    chats = await db.chats.get_user_chats(user_id, pagen.limit, pagen.offset)


@router.post('/{chat_id}')
async def set_chat(chat_id: int, request: Request, db: PgSqlDep):
    ...
