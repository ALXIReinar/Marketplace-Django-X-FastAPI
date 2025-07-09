from core.config_dir.config import env
from core.config_dir.logger import log_event

cutter_types = {
    2: 'video/mp4',
    3: 'audio/mpeg',
}
def content_cutter(file_name):
    log_event('Нарезаем файл: %s', file_name)
    with open(f'.{env.local_storage}/{file_name}', 'rb') as file:
        while chunk:= file.read(1024 * 1024):
            yield chunk
