FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    netcat-traditional \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --upgrade pip && pip install -r /app/requirements/base.txt

COPY src /app/src
COPY compose /compose

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

ENTRYPOINT ["/compose/django/entrypoint.sh"]
