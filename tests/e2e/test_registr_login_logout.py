import pytest

from core.config_dir.config import env
from core.config_dir.logger import log_event


@pytest.mark.parametrize(
    'reg_status_code',
    [
        200,
        409,
    ]
)
@pytest.mark.asyncio
async def test_full_cycle_enter_process(prod_ac, xff_ip, reg_status_code):
    creds = {"passw": "Pa$$w0rd", "email": "test_user5@example.com"}
    reg_request = await prod_ac.post(
        '/api/public/users/sign_up',
        headers=xff_ip,
        json=creds
    )
    assert reg_request.status_code == reg_status_code
    if reg_request.status_code == 409:
        return

    log_in = await prod_ac.post(
        '/api/public/users/login',
        headers=xff_ip,
        json=creds
    )
    assert log_in.status_code == 200
    logout = await prod_ac.put(
        '/api/private/users/logout',
        headers=xff_ip,
        cookies=log_in.cookies
    )
    assert logout.status_code == 200 and len(logout.cookies) == 0

    db_check_user = await prod_ac.post(
        env.pg_api_db,
        json={'query': 'select id from users where email = $1', 'method': 'fetchrow', 'args': [creds['email']]}
    )
    db_logout_check = await prod_ac.post(
        env.pg_api_db,
        json={'query': 'select session_id from sessions_users where user_id = $1', 'method': 'fetchrow', 'args': [6]}
    )
    assert db_check_user.json()['result'].get('id') == 6 and db_logout_check.json()['result'] is None
