from core.config_dir.config import env


def content_cutter(file_name):
    path = env.local_storage + file_name
    with open(path, 'rb') as file:
        while chunk:= file.read(1024 * 1024):
            yield chunk
