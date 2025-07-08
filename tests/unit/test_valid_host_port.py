import pytest

from core.config_dir.config import get_host_port_password_DB, env, get_env_vars, get_host_port_ES, get_host_port_REDIS, \
    get_host_port_Rmq, get_uvicorn_host
from tests.unit.conftest import replace_environment


class TestConnectivePairs:
    @pytest.mark.parametrize(
        'env_pack, waited_vals',
        [
         ({'CLOUD_DB': '0', 'DOCKER_DB': '0', 'DOCKERIZED': '0', 'CELERY_WORKER': '0'},
          (env.pg_password, env.pg_host, env.pg_port)),
         ({'CLOUD_DB': '0', 'DOCKER_DB': '0', 'DOCKERIZED': '1', 'CELERY_WORKER': '1'},
          (env.pg_password, env.internal_host, env.pg_port)),
        # Локальная БД и Селери в докере
         ({'CLOUD_DB': '1', 'DOCKER_DB': '0', 'DOCKERIZED': '0', 'CELERY_WORKER': '0'},
          (env.pg_password_cl, env.pg_host_cl, env.pg_port_cl)),
         ({'CLOUD_DB': '1', 'DOCKER_DB': '0', 'DOCKERIZED': '1', 'CELERY_WORKER': '1'},
          (env.pg_password_cl, env.pg_host_cl, env.pg_port_cl)),
        # Облачная БД
         ({'CLOUD_DB': '0', 'DOCKER_DB': '1', 'DOCKERIZED': '0', 'CELERY_WORKER': '0'},
          (env.pg_password, env.pg_host, env.pg_port_docker)),
         ({'CLOUD_DB': '0', 'DOCKER_DB': '1', 'DOCKERIZED': '1', 'CELERY_WORKER': '1'},
          (env.pg_password, env.pg_host_celery_worker_docker_db, env.pg_port)),
        # БД в докере
         ({'CLOUD_DB': '0', 'DOCKER_DB': '0', 'DOCKERIZED': '1', 'CELERY_WORKER': '0', 'DEPLOYED': '1'},
          (env.pg_password, env.pg_host_docker, env.pg_port)),
         ({'CLOUD_DB': '0', 'DOCKER_DB': '0', 'DOCKERIZED': '1', 'CELERY_WORKER': '1', 'DEPLOYED': '1'},
          (env.pg_password, env.pg_host_docker, env.pg_port)),
        # Фулл деплой
    ])
    def test_db_pairs(self, env_pack, waited_vals):
        replace_environment(env_pack)
        real_values = tuple(get_host_port_password_DB(get_env_vars()).values())
        assert real_values == waited_vals

    @pytest.mark.parametrize(
        'env_pack, waited_vals',
        [
         ({'DOCKER_ES': '0', 'DOCKERIZED': '0'},
          ((env.elastic_user, env.elastic_password), env.elastic_cert, False, [f'https://{env.elastic_host}:{env.elastic_port}'])),
         ({'DOCKER_ES': '0', 'DOCKERIZED': '1'},
          ((env.elastic_user, env.elastic_password), env.elastic_cert_docker, False, [f'https://{env.internal_host}:{env.elastic_port}'])),
        # Эластик на локалке
         ({'DOCKER_ES': '1', 'DOCKERIZED': '0'},
          ([f'http://{env.elastic_host}:{env.elastic_port}'],)),
         ({'DOCKER_ES': '1', 'DOCKERIZED': '1'},
          ([f'http://{env.elastic_host_docker}:{env.elastic_port}'],)),
        # Эластик в Докере/Фулл Деплой
    ])
    def test_es_pairs(self, env_pack, waited_vals):
        replace_environment(env_pack)
        real_values = tuple(get_host_port_ES(get_env_vars()).values())
        assert real_values == waited_vals

    @pytest.mark.parametrize(
        'env_pack, waited_vals',
        [
            ({'DOCKERIZED': '0'}, (env.redis_host, env.redis_port)),
            ({'DOCKERIZED': '1'}, (env.redis_host_docker, env.redis_port_docker)),
    ])
    def test_redis_pairs(self, env_pack, waited_vals):
        replace_environment(env_pack)
        real_values = tuple(get_host_port_REDIS(get_env_vars()).values())
        assert real_values == waited_vals

    @pytest.mark.parametrize(
        'env_pack, waited_vals',
        [
            ({'DOCKERIZED': '0', 'DEPLOYED': '0'}, env.uvicorn_host),
            ({'DOCKERIZED': '1', 'DEPLOYED': '0'}, env.internal_host),
            ({'DOCKERIZED': '0', 'DEPLOYED': '1', 'CELERY_WORKER': '1'}, env.uvicorn_host_docker),
    ])
    def test_bg_url_pairs(self, env_pack, waited_vals):
        replace_environment(env_pack)
        real_values = get_uvicorn_host(get_env_vars())
        assert real_values == waited_vals

    @pytest.mark.parametrize(
        'env_pack, waited_vals',
        [
            ({'DOCKERIZED': '0'}, (env.rabbitmq_host, env.rabbitmq_port_docker, env.rabbitmq_user, env.rabbitmq_passw)),
            ({'DOCKERIZED': '1'}, (env.rabbitmq_host_docker, env.rabbitmq_port_docker, env.rabbitmq_user, env.rabbitmq_passw)),
    ])
    def test_rabbit_pairs(self, env_pack, waited_vals):
        replace_environment(env_pack)
        real_values = tuple(get_host_port_Rmq(get_env_vars()).values())
        assert real_values == waited_vals
