from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from core.schemas.product_schemas import PaginationSchema


class WSControl(str, Enum):
    open = 'view_chat'
    ws_chat_channel = 'chat'
    send_msg = 'send_msg'
    last_messages = 'last_messages_layout'
    get_file = 'get_file'
    get_chunks_file = 'get_chunks_file'
    save_file_local = 'save_file_fs'
    save_file_cloud = 'save_file_s3'
    presigned_url = 'get_s3-obj_url'
    set_readed = 'set_readed'
    commit_msg = 'commit_msg'



class WSOpenCloseSchema(BaseModel):
    event: Literal[WSControl.open]
    chat_id: int
    user_id: None | int

class WSMessageSchema(BaseModel):
    """
    chat_messages:
     - type: 1 - text
             2 - media
             3 - audio
             4 - doc/other
    """
    event: Literal[WSControl.send_msg]
    chat_id: int
    type: Literal[1, 2, 3, 4]
    text_field: str | None
    reply_id: int | None

class PaginationChatMessSchema(PaginationSchema):
    limit: int = 40
    ws_token: str


class ChatSaveFiles(WSMessageSchema):
    event: Literal[WSControl.save_file_cloud, WSControl.save_file_local]
    file_name: str

class WSFileSchema(BaseModel):
    event: Literal[WSControl.get_file]
    msg_type: Literal[2, 4]
    file_path: str

class WSFileChunksSchema(BaseModel):
    event: Literal[WSControl.get_chunks_file]
    msg_type: Literal[2, 3]
    file_path: str


class WSReadUpdateSchema(BaseModel):
    event: Literal[WSControl.set_readed]
    chat_id: int
    user_id: int
    msg_id: int


class WSCommitMsgSchema(BaseModel):
    event: Literal[WSControl.commit_msg]
    chat_id: int
    msg_id: int

class WSPresignedLinkSchema(BaseModel):
    event: Literal[WSControl.presigned_url]
    chat_id: int
    file_keys: list[str]

class WSPingS3Schema(BaseModel):
    key: str
    timeout: float = Field(default=90.0)
    interval: float = Field(default=1.5)