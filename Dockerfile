FROM python:3.13-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git unzip wget ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./server ./server

ENV PYTHONPATH=/app

CMD ["fastmcp", "run", "server/main.py", "--transport", "http", "--host", "0.0.0.0", "--port", "9000"] 