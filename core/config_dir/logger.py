import os
import inspect
from pathlib import Path

import logging
from logging.config import dictConfig

from starlette.requests import Request
from starlette.websockets import WebSocket

from core.config_dir.config import WORKDIR
from core.utils.anything import create_log_dirs, Events
from core.utils.processing_data.ip_taker import get_client_ip

create_log_dirs()
LOG_DIR = Path(WORKDIR) / 'logs'



class InfoWarningFilter(logging.Filter):
    def logger_filter(self, log):
        return log.levelno in (logging.INFO, logging.WARNING, logging.ERROR)

class ErrorFilter(logging.Filter):
    def logger_filter(self, log):
        return log.levelno == logging.CRITICAL

class DebugFilter(logging.Filter):
    def logger_filter(self, log):
        return log.levelno == logging.DEBUG

lvls = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

logger_settings = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)-8s%(reset)s | "
                      "\033[32mD%(asctime)s\033[0m | "
                      "\033[34m%(method)s\033[0m \033[36m%(url)s\033[0m | "
                      "%(cyan)s%(location)s:%(reset)s def %(cyan)s%(func)s%(reset)s(): line - %(cyan)s%(line)d%(reset)s - \033[34m%(ip)s\033[0m "
                      "%(message)s",
            "datefmt": "%d-%m-%Y T%H:%M:%S",
            "log_colors": {
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red"
            }
        },
        "no_color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(levelname)-8s | "
                      "D%(asctime)s | "
                      "%(method)s %(url)s | "
                      "%(location)s: def %(func)s(): line - %(line)d - %(ip)s "
                      "%(message)s",
            "datefmt": "%d-%m-%Y T%H:%M:%S",
            "log_colors": {
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red"
            }
        }
    },
    "filters": {
        "info_warning_error_filter": {
            "()": InfoWarningFilter,
        },
        "error_filter": {
            "()": ErrorFilter,
        },
        "debug_filter": {
            "()": DebugFilter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG"
        },
        "debug_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "DEBUG",
            "formatter": "no_color",
            "filename": LOG_DIR / "debug" / "app.log",
            "when": "midnight",
            "backupCount": 60,
            "encoding": "utf8",
            "filters": ["debug_filter"]
        },
        "info_warning_errors_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "no_color",
            "filename": LOG_DIR / "info_warning_error" / "app.log",
            "when": "midnight",
            "backupCount": 60,
            "encoding": "utf8",
            "filters": ["info_warning_error_filter"]
        },
        "critical_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "CRITICAL",
            "formatter": "no_color",
            "filename": LOG_DIR / "critical" / "app.log",
            "when": "midnight",
            "backupCount": 180,
            "encoding": "utf8",
            "filters": ["error_filter"]
        }
    },
    "loggers": {
        "prod_log": {
            "handlers": ["console", "info_warning_errors_file", "critical_file", "debug_file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

logging.config.dictConfig(logger_settings)
logger = logging.getLogger('prod_log')


def log_event(event: Events | str, *args, request: Request | WebSocket=None, level: str='INFO'):
    cur_call = inspect.currentframe()
    outer = inspect.getouterframes(cur_call)[1]
    filename = os.path.relpath(outer.filename)
    func = outer.function
    line = outer.lineno

    meth, url, ip = '', '', ''
    if isinstance(request, Request):
        meth, url, ip = request.method, request.url, get_client_ip(request)
    elif isinstance(request, WebSocket):
        url, ip = request.url, get_client_ip(request)

    message = event % args if args else event

    logger.log(lvls[level.upper()], message, extra={
        'method': meth,
        'location': filename,
        'func': func,
        'line': line,
        'url': url,
        'ip': ip
    })
