from datetime import datetime

from core.config_dir.config import get_env_vars


def add_ttl_limit(data: dict, long_ttl: bool=False):
    created_at = datetime.utcnow()

    ttl = get_env_vars().JWTs.ttl_aT
    if long_ttl:
        ttl = get_env_vars().JWTs.ttl_rT
    expired_at = created_at + ttl

    data.update(
        iat=created_at,
        exp=expired_at
    )
    return data
