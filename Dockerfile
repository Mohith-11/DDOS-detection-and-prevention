FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server/requirements.txt /app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r /app/requirements.txt

COPY server /app/server

ENV PORT 8000
EXPOSE 8000

CMD sh -c "gunicorn server.wsgi:app -k gevent -w 1 -b 0.0.0.0:"
