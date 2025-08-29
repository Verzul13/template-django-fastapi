import logging

from celery import shared_task

logger = logging.getLogger("logger")


@shared_task
def test_task():
    logger.info(">>> Periodic test_task executed!")
    return "ok"
