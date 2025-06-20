from typing import Literal

from pydantic import BaseModel

from core.schemas.product_schemas import PaginationSchema


class WSContractSchema(BaseModel):
    event: Literal['view_chat', 'close_chat', 'last_messages_layout', 'send_msg', 'get_file', 'save_file']

class WSOpenCloseSchema(WSContractSchema):
    chat_id: int

class WSMessageSchema(WSOpenCloseSchema):
    """
    chat_messages:
     - type: 1 - text
             2 - media
             3 - audio
             4 - doc/other
    """
    type: Literal[1, 2, 3, 4]
    text_field: str | None
    reply_id: int | None

class PaginationChatMessSchema(PaginationSchema):
    limit: int = 40
    ws_token: str


class ChatSaveFiles(WSMessageSchema):
    file_name: str

class WSFileSchema(WSContractSchema):
    msg_type: Literal[1, 2, 3, 4]
    file_path: str
