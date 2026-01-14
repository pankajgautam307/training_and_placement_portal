FROM python:3.13-slim

# Install system deps for cairo and pycairo
RUN apt-get update && apt-get install -y \
    libcairo2 libcairo2-dev libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN python -m venv .venv \
    && . .venv/bin/activate \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1


# Railway will inject PORT
ENV PORT=8000

CMD python init_db.py && gunicorn app:app --bind 0.0.0.0:${PORT}
