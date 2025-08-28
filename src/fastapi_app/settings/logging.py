# fastapi_app/settings/logging.py
import functools
import inspect
import logging
import os
from logging.config import dictConfig

from fastapi.concurrency import run_in_threadpool

try:
    from udp_logger.apm.udp_apm import UdpAsyncAPMHandler
    UDP_LIB_AVAILABLE = True
except Exception:
    UdpAsyncAPMHandler = None  # type: ignore
    UDP_LIB_AVAILABLE = False

UDP_HOST = os.getenv("UDP_LOG_HOST", "").strip()
UDP_PORT = int(os.getenv("UDP_LOG_PORT", "9999"))
SERVER_NAME = os.getenv("SERVER_NAME", "django-fastapi")

USE_UDP = bool(UDP_HOST) and UDP_LIB_AVAILABLE

# ---------- BASE (без UDP) ----------


def build_base_logging_config():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple":  {"format": "%(levelname)s %(message)s"},
            "verbose": {"format": "%(levelname)s %(asctime)s %(name)s %(message)s"},
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "logger":        {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn":       {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "fastapi":       {"handlers": ["console"], "level": "INFO", "propagate": False},
        },
    }


def setup_logging():
    dictConfig(build_base_logging_config())


# ---------- LATE UDP ATTACH ----------
_udp_enabled = False


def enable_udp_logging():
    """
    Подключаем UDP-хендлер ПОСЛЕ старта воркера (в lifespan.startup).
    Остаётся ваш UDPSyncLoggerHandler.
    """
    global _udp_enabled
    if _udp_enabled or not USE_UDP:
        return

    # Создаём хендлер экземпляром (dictConfig уже отработал)
    from udp_logger.logger.udp_handler import UDPSyncLoggerHandler
    udp_handler = UDPSyncLoggerHandler(
        udp_host=UDP_HOST,
        udp_port=UDP_PORT,
        server_name=SERVER_NAME,
    )

    # Подвешиваем к нужным логгерам
    for name in ("logger", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(name)
        # чтобы не плодить дубликаты
        if not any(type(h).__name__ == type(udp_handler).__name__ for h in lg.handlers):
            lg.addHandler(udp_handler)

    _udp_enabled = True


# ---------- APM decorator ----------
_udp_apm_instance = None


def _get_apm_handler():
    global _udp_apm_instance
    if not USE_UDP:
        return None
    if _udp_apm_instance is None:
        _udp_apm_instance = UdpAsyncAPMHandler(
            udp_host=UDP_HOST,
            udp_port=UDP_PORT,
            server_name=SERVER_NAME,
        )
    return _udp_apm_instance


def apm(func):
    handler = _get_apm_handler()
    if handler is None:
        return func
    if inspect.iscoroutinefunction(func):
        return handler.apm(func)

    @functools.wraps(func)
    async def _async_wrapper(*args, **kwargs):
        return await run_in_threadpool(func, *args, **kwargs)
    return handler.apm(_async_wrapper)
