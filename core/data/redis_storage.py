from aioredis import Redis

from core.config_dir.config import get_env_vars

redis = Redis(host=get_env_vars().redis_host)