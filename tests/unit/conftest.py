import pytest
from fastapi import HTTPException

from core.config_dir.config import env
from core.config_dir.logger import log_event
from core.schemas.chat_schema import ChatSaveFiles
from contextlib import nullcontext as no_raises


def get_schemas_and_raw_json():
    schemas_raw_data_exception = [
        (
            ChatSaveFiles,
            '{"event":"save_file_fs","chat_id":4,"type":2,"text_field":null,"reply_id":null,"file_name":"example.png"}',
            no_raises()
         ),
        (
            ChatSaveFiles,
            '{"EVENT":"save_file_local","chat_id":4,"type":2,"text_field":null,"reply_id":null,"file_name":"example.png"}',
            pytest.raises(HTTPException)
        ),
        (
            ChatSaveFiles,
            '{"chat_id":4,"type":2,"text_field":null,"reply_id":null,"file_name":"example.png"}',
            pytest.raises(HTTPException)
        )
    ]
    return schemas_raw_data_exception

def get_token_list(with_ttl: bool):
    token_list = [
        'access_token',
        'refresh_token',
        'ws_token',
    ]
    ttl_list = [
        env.JWTs.ttl_aT,
        env.JWTs.ttl_rT,
        env.JWTs.ttl_wT,
    ]
    if with_ttl:
        archive = list(zip(token_list, ttl_list))
        return archive
    return token_list
