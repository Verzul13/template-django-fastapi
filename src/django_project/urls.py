import logging

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

logger = logging.getLogger("logger")


def health(_request):
    return JsonResponse({"status": "ok", "app": "django"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
