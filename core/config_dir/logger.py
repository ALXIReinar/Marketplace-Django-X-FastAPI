import sys
from pathlib import Path
from loguru import logger

from core.utils.anything import Events
from core.config_dir.config import WORKDIR

from fastapi import Request


LOG_DIR = Path(WORKDIR) / 'logs'
logger.remove()


def warning_info_logging(log):
    return log['level'].name == 'INFO' or log['level'].name == 'WARNING'


logger.add(
    sys.stdout,
    colorize=True,
    level='DEBUG',
    format="<green>D{time:YYYY-MM-DD} T{time:HH:mm:ss}</green> | "
           "<blue>{extra[method]}</blue> <cyan>{extra[url]}</cyan> <magenta>{extra[status]}</magenta> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>: def <cyan>{function}</cyan>(): line - <cyan>{line}</cyan> - "
           "<level>{message}; {extra[ip]} {extra[user_id]} {extra[s_id]} {extra[email]} {extra[name]}</level>"
)

logger.add(
    LOG_DIR / 'all_wo_errs' /'{time:DD-MM-YYYY}.log',
    rotation='1 week',
    retention='4 weeks',
    compression='zip',
    filter=warning_info_logging,
    level='INFO',
    encoding='UTF-8',
    enqueue=True,
    format="<green>D{time:YYYY-MM-DD} T{time:HH:mm:ss}</green> | "
           "<blue>{extra[method]}</blue> <cyan>{extra[url]}</cyan> <magenta>{extra[status]}</magenta> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>: def <cyan>{function}</cyan>(): line - <cyan>{line}</cyan> - "
           "<level>{message}; {extra[ip]} {extra[user_id]} {extra[s_id]} {extra[email]} {extra[name]}</level>"
)

logger.add(
    LOG_DIR / 'errors' / '{time:DD-MM-YYYY}.log',
    rotation='1 month',
    retention='6 months',
    compression='zip',
    level='ERROR',
    encoding='UTF-8',
    enqueue=True,
    format="<green>D{time:YYYY-MM-DD} T{time:HH:mm:ss}</green> | "
           "<blue>{extra[method]}</blue> <cyan>{extra[url]}</cyan> <magenta>{extra[status]}</magenta> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>: def <cyan>{function}</cyan>(): line - <cyan>{line}</cyan> - "
           "<level>{message}; {extra[ip]} {extra[user_id]} {extra[s_id]} {extra[email]} {extra[name]}</level>"
)


def log_event(event: Events, request: Request, level: str='INFO', **extra):
    logger.bind(
        method=request.method,
        url=request.url,
        ip=request.client.host,
        **extra
    ).log(level, event)