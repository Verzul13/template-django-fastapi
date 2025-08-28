#!/usr/bin/env bash
set -e
# Запуск Gunicorn (Django WSGI)
exec gunicorn django_project.wsgi:application --config /compose/django/gunicorn.conf.py
