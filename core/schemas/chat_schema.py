from typing import Literal

from pydantic import BaseModel

from core.schemas.product_schemas import PaginationSchema


class WSContractSchema(BaseModel):
    event: Literal['view_chat', 'close_chat', 'msg_contract']

class WSOpenCloseSchema(WSContractSchema):
    chat_id: int

class WSMessageSchema(WSContractSchema):
    """
    chat_messages:
     - type: 1 - text
             2 - media
             3 - audio
    """
    chat_id: int
    type: Literal[1, 2, 3]
    text_field: str | None
    reply_id: int | None

class PaginationChatMessSchema(PaginationSchema):
    limit: int = 40
    ws_token: str