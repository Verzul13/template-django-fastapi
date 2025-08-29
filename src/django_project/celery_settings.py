import os

from django_project.settings import TIME_ZONE

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "amqp://rabbitmq:5672//")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "django-db")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 min
# CELERY_BEAT_SCHEDULE = {
#     "test-task-every-30s": {
#         "task": "apps.core.tasks.test_task",  # путь к задаче
#         "schedule": 30.0,  # каждые 30 секунд
#     },
# }
