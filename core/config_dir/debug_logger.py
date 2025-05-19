import inspect
import os
import sys
from pathlib import Path

from loguru import logger

from core.config_dir.config import WORKDIR
from core.utils.anything import create_debug_log_dir



create_debug_log_dir()
LOG_DIR = Path(WORKDIR) / 'logs' / 'debug'
logger.remove()


def debug_safe_format(log):
    extra = log['extra']

    method = extra.get('method', '')
    url = extra.get('url', '')
    status = extra.get('status', '')

    location = extra.get('caller_file', log['name'])
    func = extra.get('caller_func', log['function'])
    line = extra.get('caller_line', log['line'])

    return (
        f"<green>D{log['time']:YYYY-MM-DD} T{log['time']:HH:mm:ss}</green> | "
        f"<blue>{method}</blue> <cyan>{url}</cyan> <magenta>{status}</magenta> | "
        f"<level>{log['level']: <8}</level> | "
        f"<cyan>{location}</cyan>: def <cyan>{func}</cyan>(): line - <cyan>{line}</cyan> - "
        f"<level>{log['message']}\n"
    )

logger.add(
    sys.stdout,
    level='DEBUG',
    colorize=True,
    format=debug_safe_format
)


logger.add(
    LOG_DIR / '{time:DD-MM-YYYY}.log',
    level='DEBUG',
    encoding='UTF-8',
    rotation='1 day',
    retention='6 months',
    compression='zip',
    enqueue=True,
    format=debug_safe_format
)

def log_debug(message, level='DEBUG', **extra):
    cur_call = inspect.currentframe()
    outer = inspect.getouterframes(cur_call)[1]
    filename = os.path.relpath(outer.filename)
    func = outer.function
    line = outer.lineno

    logger.bind(
        caller_file=filename,
        caller_func=func,
        caller_line=line,
        **extra
    ).log(level, f'{message}')
