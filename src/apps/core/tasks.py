from time import sleep

from celery import shared_task


@shared_task
def add(x: int, y: int) -> int:
    """Пример простой задачи."""
    sleep(1)
    return x + y
