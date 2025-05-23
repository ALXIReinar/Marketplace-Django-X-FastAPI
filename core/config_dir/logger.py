import inspect
import os.path
import sys
from pathlib import Path
from loguru import logger

from core.config_dir.config import WORKDIR
from core.utils.anything import Events, create_log_dirs

from fastapi import Request


create_log_dirs()
LOG_DIR = Path(WORKDIR) / 'logs'

logger.remove()


def warning_info_logging(log):
    return log['level'].name == 'INFO' or log['level'].name == 'WARNING'

def safe_format(log):
    extra = log['extra']

    method = extra.get('method', '')
    url = extra.get('url', '')
    status = extra.get('status', '')
    ip = extra.get('ip', '')
    user_id = extra.get('user_id', '')
    s_id = extra.get('s_id', '')
    email = extra.get('email', '')
    name = extra.get('name', '')

    location = extra.get('caller_file', log['name'])
    func = extra.get('caller_func', log['function'])
    line = extra.get('caller_line', log['line'])

    return (
        f"<green>D{log['time']:YYYY-MM-DD} T{log['time']:HH:mm:ss}</green> | "
        f"<blue>{method}</blue> <cyan>{url}</cyan> <magenta>{status}</magenta> | "
        f"<level>{log['level']: <8}</level> | "
        f"<cyan>{location}</cyan>: def <cyan>{func}</cyan>(): line - <cyan>{line}</cyan> - "
        f"<level>{log['message']}; {ip} {user_id} {s_id} {email} {name}</level>\n"
    )

logger.add(
    sys.stdout,
    colorize=True,
    level='DEBUG',
    format=safe_format
)

logger.add(
    LOG_DIR / 'info_warning' /'{time:DD-MM-YYYY}.log',
    rotation='1 week',
    retention='4 weeks',
    compression='zip',
    filter=warning_info_logging,
    level='INFO',
    encoding='UTF-8',
    enqueue=True,
    format=safe_format
)

logger.add(
    LOG_DIR / 'errors' / '{time:DD-MM-YYYY}.log',
    rotation='1 month',
    retention='6 months',
    compression='zip',
    level='ERROR',
    encoding='UTF-8',
    enqueue=True,
    format=safe_format
)


def log_event(event: Events, request: Request, level: str='INFO', **extra):
    cur_call = inspect.currentframe()
    outer = inspect.getouterframes(cur_call)[1]
    filename = os.path.relpath(outer.filename)
    func = outer.function
    line = outer.lineno

    logger.bind(
        caller_file=filename,
        caller_func=func,
        caller_line=line,

        method=request.method,
        url=request.url,
        ip=request.client.host,
        **extra
    ).log(level, event)