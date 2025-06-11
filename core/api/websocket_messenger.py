from fastapi import APIRouter
from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.base_dependencies import PagenChatDep
from core.data.postgre import PgSqlDep
from core.schemas.user_schemas import WSOpenCloseSchema
from core.utils.anything import Tags, WSControl

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
    chats = await db.chats.get_user_chats(request.state.user_id, pagen.limit, pagen.offset)
    return {'chat_previews': chats}


@router.websocket('/{chat_id}')
async def ws_control(contract_obj: WSOpenCloseSchema, ws: WebSocket, request: Request, db: PgSqlDep):
    if contract_obj.event == WSControl.open:
        await ws.accept()
        try:

