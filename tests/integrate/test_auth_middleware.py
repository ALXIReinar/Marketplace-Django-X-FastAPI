import pytest


@pytest.mark.asyncio
async def test_auth_control_accept_session(ac):
    res = ac.get('/')