from aioredis import Redis

from core.config_dir.config import env

redis = Redis(host=env.redis_host if not env.dockerized else env.redis_host_docker,
              port=env.redis_port if not env.dockerized else env.redis_port_docker)